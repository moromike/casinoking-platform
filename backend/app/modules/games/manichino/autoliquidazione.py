from __future__ import annotations

from decimal import Decimal

import psycopg

from app.modules.platform.access_sessions.registro_liquidazione import registra_liquidazione
from app.modules.platform.game_codes import GAME_CODE_MANICHINO
from app.modules.platform.rounds.service import (
    build_timeout_cashout_idempotency_key,
    settle_game_round_win,
)


def _auto_cashout_active_manichino_round(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT pr.id
        FROM platform_rounds pr
        WHERE pr.access_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
        ORDER BY pr.created_at DESC
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None

    cursor.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))",
        (str(row["id"]),),
    )

    cursor.execute(
        """
        SELECT
            pr.id,
            pr.bet_amount
        FROM platform_rounds pr
        WHERE pr.access_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
        ORDER BY pr.created_at DESC
        FOR UPDATE OF pr
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    round_row = cursor.fetchone()
    if round_row is None:
        return None

    payout_amount = Decimal(round_row["bet_amount"]).quantize(Decimal("0.000001"))
    auto_cashout_key = build_timeout_cashout_idempotency_key(
        game_code=GAME_CODE_MANICHINO,
        user_id=user_id,
        access_session_id=access_session_id,
        round_id=str(round_row["id"]),
    )
    settlement_result = settle_game_round_win(
        cursor=cursor,
        game_code=GAME_CODE_MANICHINO,
        user_id=user_id,
        game_session_id=str(round_row["id"]),
        payout_amount=payout_amount,
        safe_reveals_count=0,
        idempotency_key=auto_cashout_key,
        settlement_kind="refund_no_progress",
    )
    return {
        "game_code": GAME_CODE_MANICHINO,
        "game_session_id": str(round_row["id"]),
        "status": "won",
        "settlement_mode": "refund",
        "payout_amount": f"{payout_amount:.6f}",
        "wallet_balance_after": f"{Decimal(settlement_result['wallet_balance_after']):.6f}",
        "ledger_transaction_id": str(settlement_result["ledger_transaction_id"]),
    }


registra_liquidazione(GAME_CODE_MANICHINO, _auto_cashout_active_manichino_round)
