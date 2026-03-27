from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.games.mines.exceptions import (
    MinesGameStateConflictError,
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesValidationError,
)
from app.modules.games.mines.fairness import create_fairness_artifacts
from app.modules.games.mines.round_gateway import (
    get_existing_cashout_by_key,
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
) -> dict[str, object]:
    bet_amount_decimal = _parse_bet_amount(bet_amount)
    normalized_wallet_type = wallet_type.strip().lower()
    request_fingerprint = _build_request_fingerprint(
        user_id=user_id,
        grid_size=grid_size,
        mine_count=mine_count,
        bet_amount=bet_amount_decimal,
        wallet_type=normalized_wallet_type,
    )

    if not supports_configuration(grid_size=grid_size, mine_count=mine_count):
        raise MinesValidationError("The selected grid_size and mine_count are not supported")

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
                    session_id=session_id,
                    idempotency_key=idempotency_key,
                    grid_size=grid_size,
                    mine_count=mine_count,
                    bet_amount=bet_amount_decimal,
                    wallet_type=normalized_wallet_type,
                )
                cursor.execute(
                    """
                    INSERT INTO game_sessions (
                        id,
                        user_id,
                        game_code,
                        wallet_account_id,
                        wallet_type,
                        start_ledger_transaction_id,
                        idempotency_key,
                        request_fingerprint,
                        grid_size,
                        mine_count,
                        bet_amount,
                        status,
                        safe_reveals_count,
                        revealed_cells_json,
                        mine_positions_json,
                        multiplier_current,
                        payout_current,
                        wallet_balance_after_start,
                        fairness_version,
                        nonce,
                        server_seed_hash,
                        rng_material,
                        board_hash
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        session_id,
                        user_id,
                        GAME_CODE,
                        round_open_result["wallet_account_id"],
                        normalized_wallet_type,
                        round_open_result["ledger_transaction_id"],
                        idempotency_key,
                        request_fingerprint,
                        grid_size,
                        mine_count,
                        bet_amount_decimal,
                        SESSION_STATUS_ACTIVE,
                        0,
                        "[]",
                        json.dumps(fairness_artifacts["mine_positions"]),
                        START_MULTIPLIER,
                        bet_amount_decimal,
                        round_open_result["wallet_balance_after_start"],
                        fairness_artifacts["fairness_version"],
                        fairness_artifacts["nonce"],
                        fairness_artifacts["server_seed_hash"],
                        fairness_artifacts["rng_material"],
                        fairness_artifacts["board_hash"],
                    ),
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name in {
            "ledger_transactions_idempotency_key_key",
            "game_sessions_user_idempotency_key_key",
        }:
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
        "wallet_balance_after": _format_amount(round_open_result["wallet_balance_after_start"]),
        "ledger_transaction_id": round_open_result["ledger_transaction_id"],
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
                        gs.id,
                        gs.status,
                        gs.grid_size,
                        gs.mine_count,
                        gs.bet_amount,
                        gs.wallet_type,
                        gs.safe_reveals_count,
                        gs.revealed_cells_json,
                        gs.multiplier_current,
                        gs.payout_current,
                        gs.wallet_balance_after_start,
                        gs.fairness_version,
                        gs.nonce,
                        gs.server_seed_hash,
                        gs.board_hash,
                        gs.start_ledger_transaction_id,
                        gs.created_at,
                        gs.closed_at
                    FROM game_sessions gs
                    WHERE gs.id = %s
                    """,
                    (session_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        gs.id,
                        gs.status,
                        gs.grid_size,
                        gs.mine_count,
                        gs.bet_amount,
                        gs.wallet_type,
                        gs.safe_reveals_count,
                        gs.revealed_cells_json,
                        gs.multiplier_current,
                        gs.payout_current,
                        gs.wallet_balance_after_start,
                        gs.fairness_version,
                        gs.nonce,
                        gs.server_seed_hash,
                        gs.board_hash,
                        gs.start_ledger_transaction_id,
                        gs.created_at,
                        gs.closed_at
                    FROM game_sessions gs
                    WHERE gs.id = %s
                      AND gs.user_id = %s
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
                    gs.id,
                    gs.status,
                    gs.grid_size,
                    gs.mine_count,
                    gs.bet_amount,
                    gs.wallet_type,
                    gs.safe_reveals_count,
                    gs.revealed_cells_json,
                    gs.multiplier_current,
                    gs.payout_current,
                    gs.created_at,
                    gs.closed_at
                FROM game_sessions gs
                WHERE gs.user_id = %s
                  AND gs.game_code = %s
                ORDER BY gs.created_at DESC
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
                    gs.id,
                    gs.status,
                    gs.grid_size,
                    gs.mine_count,
                    gs.fairness_version,
                    gs.nonce,
                    gs.server_seed_hash,
                    gs.board_hash,
                    gs.created_at,
                    gs.closed_at
                FROM game_sessions gs
                WHERE gs.id = %s
                  AND gs.user_id = %s
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
                    session_id=session_id,
                    wallet_account_id=str(session["wallet_account_id"]),
                    safe_reveals_count=int(session["safe_reveals_count"]),
                )
                cursor.execute(
                    """
                    UPDATE game_sessions
                    SET
                        status = %s,
                        revealed_cells_json = %s::jsonb,
                        payout_current = %s,
                        closed_at = now()
                    WHERE id = %s
                    """,
                    (
                        SESSION_STATUS_LOST,
                        json.dumps(revealed_cells),
                        Decimal("0.000000"),
                        session_id,
                    ),
                )
                return {
                    "game_session_id": session_id,
                    "status": SESSION_STATUS_LOST,
                    "result": "mine",
                    "safe_reveals_count": session["safe_reveals_count"],
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

            cursor.execute(
                """
                UPDATE game_sessions
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
                    potential_payout,
                    session_id,
                ),
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
    namespaced_idempotency_key = f"mines:cashout:{user_id}:{idempotency_key}"
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
                    session_id=session_id,
                    wallet_account_id=str(session["wallet_account_id"]),
                    payout_amount=payout_amount,
                    safe_reveals_count=int(session["safe_reveals_count"]),
                    idempotency_key=namespaced_idempotency_key,
                )
                cursor.execute(
                    """
                    UPDATE game_sessions
                    SET
                        status = %s,
                        closed_at = now()
                    WHERE id = %s
                    """,
                    (SESSION_STATUS_WON, session_id),
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name == "ledger_transactions_idempotency_key_key":
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
        "wallet_balance_after": _format_amount(settlement_result["wallet_balance_after"]),
        "ledger_transaction_id": settlement_result["ledger_transaction_id"],
    }


def session_exists(session_id: str) -> bool:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM game_sessions
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
                FROM game_sessions
                WHERE id = %s
                  AND user_id = %s
                """,
                (session_id, user_id),
            )
            row = cursor.fetchone()
    return row is not None


def _get_session_for_update(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            gs.id,
            gs.user_id,
            gs.wallet_account_id,
            gs.grid_size,
            gs.mine_count,
            gs.bet_amount,
            gs.status,
            gs.safe_reveals_count,
            gs.revealed_cells_json,
            gs.mine_positions_json,
            gs.multiplier_current,
            gs.payout_current
        FROM game_sessions gs
        WHERE gs.id = %s
          AND gs.user_id = %s
        FOR UPDATE
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
            gs.id,
            gs.status,
            gs.grid_size,
            gs.mine_count,
            gs.bet_amount,
            gs.safe_reveals_count,
            gs.multiplier_current,
            gs.wallet_balance_after_start,
            gs.start_ledger_transaction_id,
            gs.request_fingerprint
        FROM game_sessions gs
        WHERE gs.user_id = %s
          AND gs.idempotency_key = %s
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
        SELECT nextval('game_sessions_nonce_seq') AS nonce
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
    cursor.execute(
        """
        SELECT
            gs.payout_current,
            wa.balance_snapshot
        FROM game_sessions gs
        JOIN wallet_accounts wa ON wa.id = gs.wallet_account_id
        WHERE gs.id = %s
          AND gs.user_id = %s
        """,
        (session_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise MinesGameStateConflictError("Game session is not active for this user")

    return {
        "game_session_id": session_id,
        "status": SESSION_STATUS_WON,
        "payout_amount": _format_amount(row["payout_current"]),
        "wallet_balance_after": _format_amount(row["balance_snapshot"]),
        "ledger_transaction_id": cashout_transaction_id,
    }


def _build_request_fingerprint(
    *,
    user_id: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
) -> str:
    payload = json.dumps(
        {
            "user_id": user_id,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": _format_amount(bet_amount),
            "wallet_type": wallet_type,
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
    }


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _format_multiplier(value: Decimal) -> str:
    return f"{value:.4f}"
