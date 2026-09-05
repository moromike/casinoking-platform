from __future__ import annotations

from decimal import Decimal

import psycopg

from app.modules.platform.access_sessions.registro_liquidazione import registra_liquidazione
from app.modules.platform.game_codes import GAME_CODE_BOXE
from app.modules.platform.rounds.service import (
    build_timeout_cashout_idempotency_key,
    settle_game_round_win,
)


def _auto_cashout_active_boxe_round(
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
            br.safe_picks_count,
            br.multiplier_current,
            br.payout_current
        FROM platform_rounds pr
        JOIN boxe_rounds br ON br.platform_round_id = pr.id
        WHERE pr.access_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
          AND br.status IN ('created', 'active', 'row_revealed', 'cashout_pending')
        ORDER BY pr.created_at DESC
        FOR UPDATE OF pr, br
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    round_row = cursor.fetchone()
    if round_row is None:
        return None

    safe_picks_count = int(round_row["safe_picks_count"])
    payout_amount = Decimal(round_row["bet_amount"]).quantize(Decimal("0.000001"))
    settlement_mode = "refund"
    if safe_picks_count > 0:
        payout_amount = Decimal(round_row["payout_current"]).quantize(Decimal("0.000001"))
        settlement_mode = "cashout"

    auto_cashout_key = build_timeout_cashout_idempotency_key(
        game_code=GAME_CODE_BOXE,
        user_id=user_id,
        access_session_id=access_session_id,
        round_id=str(round_row["id"]),
    )
    settlement_result = settle_game_round_win(
        cursor=cursor,
        game_code=GAME_CODE_BOXE,
        user_id=user_id,
        game_session_id=str(round_row["id"]),
        payout_amount=payout_amount,
        safe_reveals_count=safe_picks_count,
        idempotency_key=auto_cashout_key,
        settlement_kind="refund_no_progress" if settlement_mode == "refund" else "auto_cashout",
    )
    cursor.execute(
        """
        UPDATE boxe_rounds
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
    return {
        "game_code": GAME_CODE_BOXE,
        "game_session_id": str(round_row["id"]),
        "status": "won",
        "settlement_mode": settlement_mode,
        "safe_picks_count": safe_picks_count,
        "multiplier_current": f"{Decimal(round_row['multiplier_current']):.4f}",
        "payout_amount": f"{payout_amount:.6f}",
        "wallet_balance_after": f"{Decimal(settlement_result['wallet_balance_after']):.6f}",
        "ledger_transaction_id": str(settlement_result["ledger_transaction_id"]),
    }


registra_liquidazione(GAME_CODE_BOXE, _auto_cashout_active_boxe_round)
