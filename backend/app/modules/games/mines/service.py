from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.games.mines.backoffice_config import is_published_configuration_supported
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesValidationError,
)
from app.modules.games.mines.fairness import create_fairness_artifacts
from app.modules.games.mines.round_gateway import (
    build_cashout_idempotency_key,
    get_cashout_snapshot,
    get_existing_cashout_by_key,
    get_round_start_snapshot,
    is_open_round_idempotency_violation,
    is_settlement_idempotency_violation,
    open_round,
    settle_round_loss,
    settle_round_win,
)
from app.modules.games.mines.runtime import get_multiplier, supports_configuration

GAME_CODE = "mines"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_WON = "won"
SESSION_STATUS_LOST = "lost"
START_MULTIPLIER = Decimal("1.0000")


def start_session(
    *,
    user_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: str,
    wallet_type: str,
    access_session_id: str | None = None,
    table_session_id: str | None = None,
) -> dict[str, object]:
    bet_amount_decimal = _parse_bet_amount(bet_amount)
    normalized_wallet_type = wallet_type.strip().lower()
    request_fingerprint = _build_request_fingerprint(
        user_id=user_id,
        grid_size=grid_size,
        mine_count=mine_count,
        bet_amount=bet_amount_decimal,
        wallet_type=normalized_wallet_type,
        access_session_id=access_session_id,
        table_session_id=table_session_id,
    )

    if not supports_configuration(grid_size=grid_size, mine_count=mine_count):
        raise MinesValidationError("The selected grid_size and mine_count are not supported")
    if not is_published_configuration_supported(grid_size=grid_size, mine_count=mine_count):
        raise MinesValidationError("The selected grid_size and mine_count are not published")

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_session = _get_existing_session_by_idempotency(
                    cursor=cursor,
                    user_id=user_id,
                    idempotency_key=idempotency_key,
                )
                if existing_session is not None:
                    if existing_session["request_fingerprint"] != request_fingerprint:
                        raise MinesIdempotencyConflictError(
                            "Idempotency key already used with a different payload"
                        )
                    return _start_response_from_existing(existing_session)

                fairness_nonce = _get_next_fairness_nonce(cursor=cursor)
                fairness_artifacts = create_fairness_artifacts(
                    cursor=cursor,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    nonce=fairness_nonce,
                )

                session_id = str(uuid4())
                round_open_result = open_round(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    idempotency_key=idempotency_key,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    wallet_type=normalized_wallet_type,
                    table_session_id=table_session_id,
                    access_session_id=access_session_id,
                )
                _insert_platform_round(
                    cursor,
                    session_id=session_id,
                    user_id=user_id,
                    access_session_id=access_session_id,
                    wallet_account_id=round_open_result.wallet_account_id,
                    wallet_type=normalized_wallet_type,
                    bet_amount=bet_amount_decimal,
                    start_ledger_transaction_id=round_open_result.ledger_transaction_id,
                    wallet_balance_after_start=round_open_result.wallet_balance_after_start,
                    table_session_id=round_open_result.table_session_id,
                    idempotency_key=idempotency_key,
                    request_fingerprint=request_fingerprint,
                )
                _insert_mines_game_round(
                    cursor,
                    session_id=session_id,
                    user_id=user_id,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    fairness_artifacts=fairness_artifacts,
                    platform_round_id=round_open_result.platform_round_id,
                )
    except psycopg.errors.UniqueViolation as exc:
        if is_open_round_idempotency_violation(exc):
            existing_session = _get_existing_session_by_idempotency_outside_tx(
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing_session is not None:
                if existing_session["request_fingerprint"] != request_fingerprint:
                    raise MinesIdempotencyConflictError(
                        "Idempotency key already used with a different payload"
                    ) from exc
                return _start_response_from_existing(existing_session)
        raise

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "grid_size": grid_size,
        "mine_count": mine_count,
        "bet_amount": _format_amount(bet_amount_decimal),
        "safe_reveals_count": 0,
        "multiplier_current": _format_multiplier(START_MULTIPLIER),
        "wallet_balance_after": _format_amount(round_open_result.wallet_balance_after_start),
        "ledger_transaction_id": round_open_result.ledger_transaction_id,
        "table_session_id": round_open_result.table_session_id,
        "table_session": round_open_result.table_session,
    }


def get_session_for_user(
    *,
    user_id: str,
    session_id: str,
    viewer_role: str = "player",
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            if viewer_role == "admin":
                cursor.execute(
                    """
                    SELECT
                        pr.id,
                        pr.status,
                        mgr.grid_size,
                        mgr.mine_count,
                        pr.bet_amount,
                        pr.wallet_type,
                        mgr.safe_reveals_count,
                        mgr.revealed_cells_json,
                        mgr.multiplier_current,
                        mgr.payout_current,
                        pr.wallet_balance_after_start,
                        pr.table_session_id,
                        mgr.fairness_version,
                        mgr.nonce,
                        mgr.server_seed_hash,
                        mgr.board_hash,
                        pr.start_ledger_transaction_id,
                        pr.created_at,
                        pr.closed_at
                    FROM platform_rounds pr
                    JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                    WHERE pr.id = %s
                    """,
                    (session_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        pr.id,
                        pr.status,
                        mgr.grid_size,
                        mgr.mine_count,
                        pr.bet_amount,
                        pr.wallet_type,
                        mgr.safe_reveals_count,
                        mgr.revealed_cells_json,
                        mgr.multiplier_current,
                        mgr.payout_current,
                        pr.wallet_balance_after_start,
                        pr.table_session_id,
                        mgr.fairness_version,
                        mgr.nonce,
                        mgr.server_seed_hash,
                        mgr.board_hash,
                        pr.start_ledger_transaction_id,
                        pr.created_at,
                        pr.closed_at
                    FROM platform_rounds pr
                    JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                    WHERE pr.id = %s
                      AND pr.user_id = %s
                    """,
                    (session_id, user_id),
                )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "wallet_type": row["wallet_type"],
        "safe_reveals_count": row["safe_reveals_count"],
        "revealed_cells": row["revealed_cells_json"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "potential_payout": _format_amount(row["payout_current"]),
        "wallet_balance_after_start": _format_amount(row["wallet_balance_after_start"]),
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
        "fairness_version": row["fairness_version"],
        "nonce": row["nonce"],
        "server_seed_hash": row["server_seed_hash"],
        "board_hash": row["board_hash"],
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def list_recent_sessions_for_user(
    *,
    user_id: str,
    limit: int = 12,
) -> list[dict[str, object]]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pr.id,
                    pr.status,
                    mgr.grid_size,
                    mgr.mine_count,
                    pr.bet_amount,
                    pr.wallet_type,
                    mgr.safe_reveals_count,
                    mgr.revealed_cells_json,
                    mgr.multiplier_current,
                    mgr.payout_current,
                    pr.access_session_id,
                    pr.table_session_id,
                    gas.game_code AS access_session_game_code,
                    gas.started_at AS access_session_started_at,
                    gas.last_activity_at AS access_session_last_activity_at,
                    gas.ended_at AS access_session_ended_at,
                    gas.status AS access_session_status,
                    pr.created_at,
                    pr.closed_at
                FROM platform_rounds pr
                JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
                LEFT JOIN game_access_sessions gas ON gas.id = pr.access_session_id
                WHERE pr.user_id = %s
                  AND pr.game_code = %s
                ORDER BY pr.created_at DESC
                LIMIT %s
                """,
                (user_id, GAME_CODE, limit),
            )
            rows = list(cursor.fetchall())

    return [
        {
            "game_session_id": str(row["id"]),
            "status": row["status"],
            "grid_size": row["grid_size"],
            "mine_count": row["mine_count"],
            "bet_amount": _format_amount(row["bet_amount"]),
            "wallet_type": row["wallet_type"],
            "safe_reveals_count": row["safe_reveals_count"],
            "revealed_cells_count": len(row["revealed_cells_json"]),
            "multiplier_current": _format_multiplier(row["multiplier_current"]),
            "potential_payout": _format_amount(row["payout_current"]),
            "access_session_id": str(row["access_session_id"]) if row["access_session_id"] else None,
            "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
            "access_session": (
                {
                    "id": str(row["access_session_id"]),
                    "game_code": row["access_session_game_code"],
                    "status": row["access_session_status"],
                    "started_at": row["access_session_started_at"].isoformat(),
                    "last_activity_at": row["access_session_last_activity_at"].isoformat(),
                    "ended_at": (
                        row["access_session_ended_at"].isoformat()
                        if row["access_session_ended_at"]
                        else None
                    ),
                }
                if row["access_session_id"]
                else None
            ),
            "created_at": row["created_at"].isoformat(),
            "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
        }
        for row in rows
    ]


def get_session_fairness_for_user(*, user_id: str, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    mgr.id,
                    pr.status,
                    mgr.grid_size,
                    mgr.mine_count,
                    mgr.fairness_version,
                    mgr.nonce,
                    mgr.server_seed_hash,
                    mgr.board_hash,
                    pr.created_at,
                    pr.closed_at
                FROM mines_game_rounds mgr
                JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
                WHERE mgr.id = %s
                  AND mgr.user_id = %s
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "fairness_version": row["fairness_version"],
        "nonce": row["nonce"],
        "server_seed_hash": row["server_seed_hash"],
        "board_hash": row["board_hash"],
        "user_verifiable": False,
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def reveal_cell(*, user_id: str, session_id: str, cell_index: int) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_session_for_update(
                cursor=cursor,
                user_id=user_id,
                session_id=session_id,
            )
            if session is None:
                raise MinesGameStateConflictError("Game session is not active for this user")
            _ensure_session_active(session)
            _validate_cell_index(cell_index=cell_index, grid_size=session["grid_size"])

            revealed_cells = list(session["revealed_cells_json"])
            if cell_index in revealed_cells:
                raise MinesGameStateConflictError("Cell already revealed")

            mine_positions = set(session["mine_positions_json"])
            if cell_index in mine_positions:
                revealed_cells.append(cell_index)
                settle_round_loss(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                )
                _close_game_round_as_lost(
                    cursor,
                    session_id=session_id,
                    revealed_cells=revealed_cells,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_LOST,
                    "result": "mine",
                    "safe_reveals_count": session["safe_reveals_count"],
                    "mine_positions": sorted(mine_positions),
                }

            revealed_cells.append(cell_index)
            safe_reveals_count = session["safe_reveals_count"] + 1
            multiplier_current = get_multiplier(
                grid_size=session["grid_size"],
                mine_count=session["mine_count"],
                safe_reveals_count=safe_reveals_count,
            )
            potential_payout = (
                session["bet_amount"] * multiplier_current
            ).quantize(Decimal("0.000001"))
            max_safe_reveals = session["grid_size"] - session["mine_count"]

            if safe_reveals_count >= max_safe_reveals:
                auto_cashout_idempotency_key = build_cashout_idempotency_key(
                    user_id=user_id,
                    idempotency_key=f"auto-final-reveal:{session_id}:{safe_reveals_count}",
                )
                settlement_result = settle_round_win(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    payout_amount=potential_payout,
                    safe_reveals_count=safe_reveals_count,
                    idempotency_key=auto_cashout_idempotency_key,
                )
                _close_game_round_as_won(
                    cursor,
                    session_id=session_id,
                    settlement_ledger_transaction_id=settlement_result.ledger_transaction_id,
                    safe_reveals_count=safe_reveals_count,
                    revealed_cells=revealed_cells,
                    multiplier_current=multiplier_current,
                    payout_current=potential_payout,
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_WON,
                    "result": "safe",
                    "safe_reveals_count": safe_reveals_count,
                    "multiplier_current": _format_multiplier(multiplier_current),
                    "potential_payout": _format_amount(potential_payout),
                    "payout_amount": _format_amount(potential_payout),
                    "wallet_balance_after": _format_amount(
                        settlement_result.wallet_balance_after
                    ),
                }

            _update_game_round_after_safe_reveal(
                cursor,
                session_id=session_id,
                safe_reveals_count=safe_reveals_count,
                revealed_cells=revealed_cells,
                multiplier_current=multiplier_current,
                payout_current=potential_payout,
            )

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_ACTIVE,
        "result": "safe",
        "safe_reveals_count": safe_reveals_count,
        "multiplier_current": _format_multiplier(multiplier_current),
        "potential_payout": _format_amount(potential_payout),
    }


def cashout_session(
    *,
    user_id: str,
    session_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    namespaced_idempotency_key = build_cashout_idempotency_key(
        user_id=user_id,
        idempotency_key=idempotency_key,
    )
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_cashout = get_existing_cashout_by_key(
                    cursor=cursor,
                    idempotency_key=namespaced_idempotency_key,
                )
                if existing_cashout is not None:
                    if str(existing_cashout["reference_id"]) != session_id:
                        raise MinesIdempotencyConflictError(
                            "Idempotency key already used with a different payload"
                        )
                    return _build_cashout_response_from_existing(
                        cursor=cursor,
                        user_id=user_id,
                        session_id=session_id,
                        cashout_transaction_id=str(existing_cashout["id"]),
                    )

                session = _get_session_for_update(
                    cursor=cursor,
                    user_id=user_id,
                    session_id=session_id,
                )
                if session is None:
                    raise MinesGameStateConflictError("Game session is not active for this user")
                if session["status"] != SESSION_STATUS_ACTIVE:
                    if session["status"] == SESSION_STATUS_WON:
                        existing_cashout = get_existing_cashout_by_key(
                            cursor=cursor,
                            idempotency_key=namespaced_idempotency_key,
                        )
                        if existing_cashout is not None:
                            if str(existing_cashout["reference_id"]) != session_id:
                                raise MinesIdempotencyConflictError(
                                    "Idempotency key already used with a different payload"
                                )
                            return _build_cashout_response_from_existing(
                                cursor=cursor,
                                user_id=user_id,
                                session_id=session_id,
                                cashout_transaction_id=str(existing_cashout["id"]),
                            )
                    raise MinesGameStateConflictError("Game session is not active")
                if session["safe_reveals_count"] <= 0:
                    raise MinesGameStateConflictError(
                        "Cashout is not available before a safe reveal"
                    )

                payout_amount = Decimal(session["payout_current"]).quantize(
                    Decimal("0.000001")
                )
                settlement_result = settle_round_win(
                    cursor=cursor,
                    user_id=user_id,
                    game_round_id=session_id,
                    payout_amount=payout_amount,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    idempotency_key=namespaced_idempotency_key,
                )
                _close_game_round_as_won(
                    cursor,
                    session_id=session_id,
                    settlement_ledger_transaction_id=settlement_result.ledger_transaction_id,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    revealed_cells=list(session["revealed_cells_json"]),
                    multiplier_current=session["multiplier_current"],
                    payout_current=payout_amount,
                )
    except psycopg.errors.UniqueViolation as exc:
        if is_settlement_idempotency_violation(exc):
            with db_connection() as connection:
                with connection.cursor() as cursor:
                    existing_cashout = get_existing_cashout_by_key(
                        cursor=cursor,
                        idempotency_key=namespaced_idempotency_key,
                    )
                    if existing_cashout is not None:
                        if str(existing_cashout["reference_id"]) != session_id:
                            raise MinesIdempotencyConflictError(
                                "Idempotency key already used with a different payload"
                            ) from exc
                        return _build_cashout_response_from_existing(
                            cursor=cursor,
                            user_id=user_id,
                            session_id=session_id,
                            cashout_transaction_id=str(existing_cashout["id"]),
                        )
        raise

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "payout_amount": _format_amount(payout_amount),
        "wallet_balance_after": _format_amount(settlement_result.wallet_balance_after),
        "ledger_transaction_id": settlement_result.ledger_transaction_id,
    }


def session_exists(session_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM mines_game_rounds
                WHERE id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
    return row is not None


def session_belongs_to_user(*, session_id: str, user_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM mines_game_rounds
                WHERE id = %s
                  AND user_id = %s
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()
    return row is not None


# ---------------------------------------------------------------------------
# Private helper functions for mines_game_rounds SQL operations.
#
# After the schema split (P4), platform fields live in platform_rounds
# (managed by platform/rounds/service.py) and game fields live in
# mines_game_rounds (managed here).
#
# Platform-field reads go through round_gateway.py which queries
# platform_rounds directly.
# ---------------------------------------------------------------------------


def _insert_mines_game_round(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    fairness_artifacts: dict[str, object],
    platform_round_id: str,
) -> None:
    """Insert a new mines_game_rounds row. Platform fields are in platform_rounds."""
    cursor.execute(
        """
        INSERT INTO mines_game_rounds (
            id,
            platform_round_id,
            user_id,
            grid_size,
            mine_count,
            safe_reveals_count,
            revealed_cells_json,
            mine_positions_json,
            multiplier_current,
            payout_current,
            fairness_version,
            nonce,
            server_seed_hash,
            rng_material,
            board_hash
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            session_id,
            platform_round_id,
            user_id,
            grid_size,
            mine_count,
            0,
            "[]",
            json.dumps(fairness_artifacts["mine_positions"]),
            START_MULTIPLIER,
            bet_amount,
            fairness_artifacts["fairness_version"],
            fairness_artifacts["nonce"],
            fairness_artifacts["server_seed_hash"],
            fairness_artifacts["rng_material"],
            fairness_artifacts["board_hash"],
        ),
    )


def _insert_platform_round(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    user_id: str,
    access_session_id: str | None,
    wallet_account_id: str,
    wallet_type: str,
    bet_amount: Decimal,
    start_ledger_transaction_id: str,
    wallet_balance_after_start: Decimal,
    table_session_id: str | None,
    idempotency_key: str,
    request_fingerprint: str,
) -> None:
    cursor.execute(
        """
        INSERT INTO platform_rounds (
            id,
            user_id,
            game_code,
            access_session_id,
            wallet_account_id,
            wallet_type,
            bet_amount,
            status,
            payout_amount,
            start_ledger_transaction_id,
            wallet_balance_after_start,
            table_session_id,
            idempotency_key,
            request_fingerprint
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            session_id,
            user_id,
            GAME_CODE,
            access_session_id,
            wallet_account_id,
            wallet_type,
            bet_amount,
            SESSION_STATUS_ACTIVE,
            Decimal("0.000000"),
            start_ledger_transaction_id,
            wallet_balance_after_start,
            table_session_id,
            idempotency_key,
            request_fingerprint,
        ),
    )


def _close_game_round_as_lost(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    revealed_cells: list[int],
) -> None:
    """Mark a mines game round as lost (mine hit)."""
    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET
            revealed_cells_json = %s::jsonb,
            payout_current = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            json.dumps(revealed_cells),
            Decimal("0.000000"),
            session_id,
        ),
    )
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = %s,
            payout_amount = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_LOST,
            Decimal("0.000000"),
            session_id,
        ),
    )


def _close_game_round_as_won(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    settlement_ledger_transaction_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    """Mark a mines game round as won (cashout or auto-cashout on final reveal)."""
    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET
            safe_reveals_count = %s,
            revealed_cells_json = %s::jsonb,
            multiplier_current = %s,
            payout_current = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            safe_reveals_count,
            json.dumps(revealed_cells),
            multiplier_current,
            payout_current,
            session_id,
        ),
    )
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = %s,
            payout_amount = %s,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (
            SESSION_STATUS_WON,
            payout_current,
            settlement_ledger_transaction_id,
            session_id,
        ),
    )


def _update_game_round_after_safe_reveal(
    cursor: psycopg.Cursor,
    *,
    session_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
    """Update mines game round state after a safe (non-mine) cell reveal."""
    cursor.execute(
        """
        UPDATE mines_game_rounds
        SET
            safe_reveals_count = %s,
            revealed_cells_json = %s::jsonb,
            multiplier_current = %s,
            payout_current = %s
        WHERE id = %s
        """,
        (
            safe_reveals_count,
            json.dumps(revealed_cells),
            multiplier_current,
            payout_current,
            session_id,
        ),
    )


def _get_session_for_update(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            mgr.id,
            mgr.user_id,
            mgr.grid_size,
            mgr.mine_count,
            pr.bet_amount,
            pr.status,
            mgr.safe_reveals_count,
            mgr.revealed_cells_json,
            mgr.mine_positions_json,
            mgr.multiplier_current,
            mgr.payout_current
        FROM mines_game_rounds mgr
        JOIN platform_rounds pr ON pr.id = mgr.platform_round_id
        WHERE mgr.id = %s
          AND mgr.user_id = %s
        FOR UPDATE OF mgr, pr
        """,
        (session_id, user_id),
    )
    return cursor.fetchone()


def _get_existing_session_by_idempotency(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            pr.id,
            pr.status,
            mgr.grid_size,
            mgr.mine_count,
            pr.bet_amount,
            mgr.safe_reveals_count,
            mgr.multiplier_current,
            pr.wallet_balance_after_start,
            pr.start_ledger_transaction_id,
            pr.table_session_id,
            pr.request_fingerprint
        FROM platform_rounds pr
        JOIN mines_game_rounds mgr ON mgr.platform_round_id = pr.id
        WHERE pr.user_id = %s
          AND pr.idempotency_key = %s
        """,
        (user_id, idempotency_key),
    )
    return cursor.fetchone()


def _get_existing_session_by_idempotency_outside_tx(
    *,
    user_id: str,
    idempotency_key: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return _get_existing_session_by_idempotency(
                cursor=cursor,
                user_id=user_id,
                idempotency_key=idempotency_key,
            )


def _get_next_fairness_nonce(*, cursor: psycopg.Cursor) -> int:
    cursor.execute(
        """
        SELECT nextval('mines_fairness_nonce_seq') AS nonce
        """
    )
    row = cursor.fetchone()
    assert row is not None
    return int(row["nonce"])


def _build_cashout_response_from_existing(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
    cashout_transaction_id: str,
) -> dict[str, object]:
    snapshot = get_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_round_id=session_id,
    )
    if snapshot is None:
        raise MinesGameStateConflictError("Game session is not active for this user")

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "payout_amount": _format_amount(snapshot["payout_current"]),
        "wallet_balance_after": _format_amount(snapshot["wallet_balance_after"]),
        "ledger_transaction_id": cashout_transaction_id,
    }


def _build_request_fingerprint(
    *,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
    access_session_id: str | None,
    table_session_id: str | None,
) -> str:
    payload = json.dumps(
        {
            "user_id": user_id,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": _format_amount(bet_amount),
            "wallet_type": wallet_type,
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _ensure_session_active(session: dict[str, object]) -> None:
    if session["status"] != SESSION_STATUS_ACTIVE:
        raise MinesGameStateConflictError("Game session is not active")


def _validate_cell_index(*, cell_index: int, grid_size: int) -> None:
    if cell_index < 0 or cell_index >= grid_size:
        raise MinesValidationError("Cell index is not valid")


def _parse_bet_amount(raw_value: str) -> Decimal:
    try:
        amount = Decimal(raw_value)
    except InvalidOperation as exc:
        raise MinesValidationError("Bet amount is not valid") from exc
    if amount <= 0:
        raise MinesValidationError("Bet amount must be greater than zero")
    return amount.quantize(Decimal("0.000001"))


def _start_response_from_existing(row: dict[str, object]) -> dict[str, object]:
    """Build the start-session response from an existing idempotent session row.

    Uses get_round_start_snapshot via round_gateway to read platform fields
    (wallet_balance_after_start, start_ledger_transaction_id) instead of
    accessing them directly from the row, keeping platform field knowledge
    encapsulated in the gateway layer.
    """
    # For the idempotent path, the row already contains the platform fields
    # from _get_existing_session_by_idempotency. We read them through the row
    # to avoid an extra DB query, but the field names are the same as what
    # get_round_start_snapshot would return.
    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "grid_size": row["grid_size"],
        "mine_count": row["mine_count"],
        "bet_amount": _format_amount(row["bet_amount"]),
        "safe_reveals_count": row["safe_reveals_count"],
        "multiplier_current": _format_multiplier(row["multiplier_current"]),
        "wallet_balance_after": _format_amount(row["wallet_balance_after_start"]),
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
        "table_session_id": str(row["table_session_id"]) if row["table_session_id"] else None,
    }


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _format_multiplier(value: Decimal) -> str:
    return f"{value:.4f}"
