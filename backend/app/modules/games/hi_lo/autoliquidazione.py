from __future__ import annotations

from decimal import Decimal
import json
from uuid import uuid4

import psycopg

from app.modules.platform.access_sessions.registro_liquidazione import registra_liquidazione
from app.modules.platform.game_codes import GAME_CODE_HI_LO
from app.modules.platform.rounds.service import (
    build_timeout_cashout_idempotency_key,
    settle_game_round_win,
)


def _auto_cashout_active_hi_lo_round(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            pr.id,
            pr.bet_amount,
            hlr.correct_predictions_count,
            hlr.multiplier_current,
            hlr.payout_current,
            hlr.current_card_rank,
            hlr.current_card_suit,
            hlr.current_draw_index
        FROM platform_rounds pr
        JOIN hi_lo_rounds hlr ON hlr.platform_round_id = pr.id
        WHERE pr.access_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
          AND hlr.status IN ('created', 'active', 'cashout_pending')
        ORDER BY pr.created_at DESC
        FOR UPDATE OF pr, hlr
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    round_row = cursor.fetchone()
    if round_row is None:
        return None

    correct_predictions_count = int(round_row["correct_predictions_count"])
    payout_amount = Decimal(round_row["bet_amount"]).quantize(Decimal("0.000001"))
    settlement_mode = "refund"
    if correct_predictions_count > 0:
        payout_amount = Decimal(round_row["payout_current"]).quantize(Decimal("0.000001"))
        settlement_mode = "cashout"

    auto_cashout_key = build_timeout_cashout_idempotency_key(
        game_code=GAME_CODE_HI_LO,
        user_id=user_id,
        access_session_id=access_session_id,
        round_id=str(round_row["id"]),
    )
    settlement_result = settle_game_round_win(
        cursor=cursor,
        game_code=GAME_CODE_HI_LO,
        user_id=user_id,
        game_session_id=str(round_row["id"]),
        payout_amount=payout_amount,
        safe_reveals_count=correct_predictions_count,
        idempotency_key=auto_cashout_key,
        settlement_kind="refund_no_progress" if settlement_mode == "refund" else "auto_cashout",
    )
    cursor.execute(
        """
        UPDATE hi_lo_rounds
        SET
            status = 'completed_cashout',
            outcome = 'cashout',
            final_payout_amount = %s,
            terminal_reason = %s,
            closed_at = now(),
            updated_at = now()
        WHERE platform_round_id = %s
        """,
        (
            payout_amount,
            (
                "auto_refund_access_session_close"
                if settlement_mode == "refund"
                else "auto_cashout_access_session_close"
            ),
            str(round_row["id"]),
        ),
    )
    _record_hi_lo_auto_cashout_action(
        cursor=cursor,
        round_id=str(round_row["id"]),
        round_row=round_row,
        payout_amount=payout_amount,
        settlement_mode=settlement_mode,
        idempotency_key=auto_cashout_key,
    )
    return {
        "game_code": GAME_CODE_HI_LO,
        "game_session_id": str(round_row["id"]),
        "status": "won",
        "settlement_mode": settlement_mode,
        "correct_predictions_count": correct_predictions_count,
        "multiplier_current": f"{Decimal(round_row['multiplier_current']):.4f}",
        "payout_amount": f"{payout_amount:.6f}",
        "wallet_balance_after": f"{Decimal(settlement_result['wallet_balance_after']):.6f}",
        "ledger_transaction_id": str(settlement_result["ledger_transaction_id"]),
    }


def _record_hi_lo_auto_cashout_action(
    *,
    cursor: psycopg.Cursor,
    round_id: str,
    round_row: dict[str, object],
    payout_amount: Decimal,
    settlement_mode: str,
    idempotency_key: str,
) -> None:
    suit = str(round_row["current_card_suit"])
    card_payload = {
        "rank": int(round_row["current_card_rank"]),
        "rank_label": _hi_lo_rank_label(int(round_row["current_card_rank"])),
        "suit": suit,
        "color": "red" if suit in {"hearts", "diamonds"} else "black",
    }
    response_payload = {
        "event": "auto_refund" if settlement_mode == "refund" else "auto_cashout",
        "round_id": round_id,
        "payout_amount": f"{payout_amount:.6f}",
    }
    cursor.execute(
        """
        INSERT INTO hi_lo_actions (
            id,
            round_id,
            action_index,
            action_type,
            prediction_action,
            success,
            probability,
            multiplier_after,
            payout_after,
            previous_card_json,
            drawn_card_json,
            draw_index,
            draw_purpose,
            rng_material,
            response_json,
            idempotency_key,
            request_fingerprint
        )
        SELECT
            %s,
            %s,
            COALESCE(MAX(action_index), -1) + 1,
            'cashout',
            NULL,
            NULL,
            NULL,
            %s,
            %s,
            %s::jsonb,
            %s::jsonb,
            %s,
            %s,
            %s,
            %s::jsonb,
            %s,
            %s
        FROM hi_lo_actions
        WHERE round_id = %s
        ON CONFLICT (round_id, idempotency_key) DO NOTHING
        """,
        (
            str(uuid4()),
            round_id,
            Decimal(round_row["multiplier_current"]),
            payout_amount,
            json.dumps(card_payload),
            json.dumps(card_payload),
            int(round_row["current_draw_index"]),
            "auto_refund_access_session_close"
            if settlement_mode == "refund"
            else "auto_cashout_access_session_close",
            "platform_access_session_close",
            json.dumps(response_payload),
            idempotency_key,
            idempotency_key,
            round_id,
        ),
    )


def _hi_lo_rank_label(rank: int) -> str:
    labels = {
        1: "A",
        11: "J",
        12: "Q",
        13: "K",
    }
    return labels.get(rank, str(rank))


registra_liquidazione(GAME_CODE_HI_LO, _auto_cashout_active_hi_lo_round)
