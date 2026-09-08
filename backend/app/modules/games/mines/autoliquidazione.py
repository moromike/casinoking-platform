from __future__ import annotations

from decimal import Decimal
import json

import psycopg

from app.modules.games.mines.state_machine import MinesRoundStatus
from app.modules.platform.access_sessions.registro_liquidazione import registra_liquidazione
from app.modules.platform.game_codes import GAME_CODE_MINES
from app.modules.platform.rounds.service import (
    build_timeout_cashout_idempotency_key,
    settle_game_round_win,
)


def _auto_cashout_active_mines_round(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
) -> dict[str, object] | None:
    # Find the active round without locking to know the round_id for
    # the advisory lock.  This avoids a deadlock with the manual cashout
    # path, which locks mines_game_rounds first and then platform_rounds.
    cursor.execute(
        """
        SELECT pr.id
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
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

    # Serialize with the manual cashout path, which acquires the same
    # advisory lock (hashtext(session_id)) before locking tables.
    cursor.execute(
        "SELECT pg_advisory_xact_lock(hashtext(%s))",
        (str(row["id"]),),
    )

    # Re-fetch under lock; the round may have been settled concurrently.
    cursor.execute(
        """
        SELECT
            pr.id,
            pr.bet_amount,
            mgr.safe_reveals_count,
            mgr.revealed_cells_json,
            mgr.multiplier_current,
            mgr.payout_current
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
        WHERE pr.access_session_id = %s
          AND pr.user_id = %s
          AND pr.status = 'active'
        ORDER BY pr.created_at DESC
        FOR UPDATE OF pr, mgr
        LIMIT 1
        """,
        (access_session_id, user_id),
    )
    round_row = cursor.fetchone()
    if round_row is None:
        return None

    safe_reveals_count = int(round_row["safe_reveals_count"])
    payout_amount = Decimal(round_row["bet_amount"]).quantize(Decimal("0.000001"))
    if safe_reveals_count > 0:
        payout_amount = Decimal(round_row["payout_current"]).quantize(Decimal("0.000001"))

    auto_cashout_key = build_timeout_cashout_idempotency_key(
        game_code=GAME_CODE_MINES,
        user_id=user_id,
        access_session_id=access_session_id,
        round_id=str(round_row["id"]),
    )

    settlement_result = settle_game_round_win(
        cursor=cursor,
        game_code=GAME_CODE_MINES,
        user_id=user_id,
        game_session_id=str(round_row["id"]),
        payout_amount=payout_amount,
        safe_reveals_count=safe_reveals_count,
        idempotency_key=auto_cashout_key,
        settlement_kind="refund_no_progress"
        if safe_reveals_count == 0
        else "auto_cashout",
    )
    _close_mines_round_as_won(
        cursor=cursor,
        round_id=str(round_row["id"]),
        safe_reveals_count=safe_reveals_count,
        revealed_cells=list(round_row["revealed_cells_json"]),
        multiplier_current=Decimal(round_row["multiplier_current"]),
        payout_current=payout_amount,
    )

    return {
        "game_code": GAME_CODE_MINES,
        "game_session_id": str(round_row["id"]),
        "status": "won",
        "settlement_mode": "refund" if safe_reveals_count == 0 else "cashout",
        "safe_reveals_count": safe_reveals_count,
        "multiplier_current": f"{Decimal(round_row['multiplier_current']):.4f}",
        "payout_amount": f"{payout_amount:.6f}",
        "wallet_balance_after": f"{Decimal(settlement_result['wallet_balance_after']):.6f}",
        "ledger_transaction_id": str(settlement_result["ledger_transaction_id"]),
    }


def _close_mines_round_as_won(
    *,
    cursor: psycopg.Cursor,
    round_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    # SIC-08: materialize mine positions and rng material at close.
    from app.modules.games.mines.repository import recompute_board_for_round

    mine_positions, rng_material = recompute_board_for_round(
        cursor,
        session_id=round_id,
    )
    cursor.execute(
        """
        -- PERCHE' CANCELLED E NON WON. La liquidazione d'ufficio restituisce la
        -- puntata: misurato l'8/09/2026 su tutte e 278 le righe interessate,
        -- incasso ESATTAMENTE uguale alla puntata. Le partite davvero vinte hanno
        -- incasso maggiore in 81 casi su 88. Marcarle 'won' metterebbe agli atti
        -- 278 vincite mai avvenute e gonfierebbe win rate e RTP.
        -- Il rilievo e' di agy in revisione indipendente, ed e' arrivato ragionando
        -- sul dominio senza nemmeno vedere il diff.
        UPDATE mines_game_rounds
        SET
            safe_reveals_count = %s,
            revealed_cells_json = %s::jsonb,
            multiplier_current = %s,
            payout_current = %s,
            mine_positions_json = %s::jsonb,
            rng_material = %s,
            status = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            safe_reveals_count,
            json.dumps(revealed_cells),
            multiplier_current,
            payout_current,
            json.dumps(mine_positions),
            rng_material,
            MinesRoundStatus.CANCELLED.value,
            round_id,
        ),
    )


registra_liquidazione(GAME_CODE_MINES, _auto_cashout_active_mines_round)
