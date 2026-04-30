from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from uuid import UUID, uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.platform.rounds.service import (
    namespace_mines_round_win_idempotency_key,
    settle_mines_round_win,
)

ACCESS_SESSION_TIMEOUT = timedelta(minutes=3)
GAME_CODE_MINES = "mines"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_CLOSED = "closed"
SESSION_STATUS_TIMED_OUT = "timed_out"


class AccessSessionValidationError(Exception):
    pass


class AccessSessionNotFoundError(Exception):
    pass


class AccessSessionStateConflictError(Exception):
    pass


def create_access_session(*, user_id: str, game_code: str) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    access_session_id = str(uuid4())

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO game_access_sessions (
                    id,
                    user_id,
                    game_code,
                    started_at,
                    last_activity_at,
                    status
                )
                VALUES (%s, %s, %s, now(), now(), %s)
                RETURNING
                    id,
                    user_id,
                    game_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                """,
                (
                    access_session_id,
                    user_id,
                    normalized_game_code,
                    SESSION_STATUS_ACTIVE,
                ),
            )
            row = cursor.fetchone()

    assert row is not None
    return _serialize_access_session(row)


def ping_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    conflict_message: str | None = None

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if session["status"] == SESSION_STATUS_ACTIVE and _is_access_session_expired(session):
                _timeout_access_session(cursor=cursor, session=session)
                conflict_message = "Access session timed out"

            if session["status"] == SESSION_STATUS_TIMED_OUT:
                conflict_message = "Access session timed out"

            if conflict_message is None and session["status"] != SESSION_STATUS_ACTIVE:
                conflict_message = "Access session is not active"

            if conflict_message is not None:
                updated_session = None
            else:
                cursor.execute(
                    """
                    UPDATE game_access_sessions
                    SET last_activity_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        user_id,
                        game_code,
                        started_at,
                        last_activity_at,
                        ended_at,
                        status
                    """,
                    (normalized_session_id,),
                )
                updated_session = cursor.fetchone()

    if conflict_message is not None:
        raise AccessSessionStateConflictError(conflict_message)

    assert updated_session is not None
    return _serialize_access_session(updated_session)


def close_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if session["status"] != SESSION_STATUS_ACTIVE:
                return _serialize_access_session(session)

            cursor.execute(
                """
                UPDATE game_access_sessions
                SET
                    last_activity_at = now(),
                    ended_at = now(),
                    status = %s
                WHERE id = %s
                RETURNING
                    id,
                    user_id,
                    game_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                """,
                (SESSION_STATUS_CLOSED, normalized_session_id),
            )
            closed_session = cursor.fetchone()

    assert closed_session is not None
    return _serialize_access_session(closed_session)


def ensure_access_session_active_for_round_start(
    *,
    user_id: str,
    access_session_id: str,
    game_code: str,
) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    normalized_game_code = _normalize_game_code(game_code)
    timed_out = False

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                game_code=normalized_game_code,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if session["status"] != SESSION_STATUS_ACTIVE:
                raise AccessSessionStateConflictError("Access session is not active")

            if _is_access_session_expired(session):
                _timeout_access_session(cursor=cursor, session=session)
                timed_out = True
            else:
                cursor.execute(
                    """
                    UPDATE game_access_sessions
                    SET last_activity_at = now()
                    WHERE id = %s
                    RETURNING
                        id,
                        user_id,
                        game_code,
                        started_at,
                        last_activity_at,
                        ended_at,
                        status
                    """,
                    (normalized_session_id,),
                )
                active_session = cursor.fetchone()

    if timed_out:
        raise AccessSessionStateConflictError("Access session timed out")

    assert active_session is not None
    return _serialize_access_session(active_session)


def _timeout_access_session(
    *,
    cursor: psycopg.Cursor,
    session: dict[str, object],
) -> tuple[dict[str, object], dict[str, object] | None]:
    auto_cashout: dict[str, object] | None = None
    if session["game_code"] == GAME_CODE_MINES:
        auto_cashout = _auto_cashout_active_mines_round(
            cursor=cursor,
            access_session_id=str(session["id"]),
            user_id=str(session["user_id"]),
        )

    cursor.execute(
        """
        UPDATE game_access_sessions
        SET
            ended_at = now(),
            status = %s
        WHERE id = %s
        RETURNING
            id,
            user_id,
            game_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        """,
        (SESSION_STATUS_TIMED_OUT, str(session["id"])),
    )
    timed_out_session = cursor.fetchone()
    assert timed_out_session is not None
    return timed_out_session, auto_cashout


def _auto_cashout_active_mines_round(
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

    auto_cashout_key = _build_timeout_cashout_idempotency_key(
        user_id=user_id,
        access_session_id=access_session_id,
        round_id=str(round_row["id"]),
    )

    settlement_result = settle_mines_round_win(
        cursor=cursor,
        user_id=user_id,
        game_session_id=str(round_row["id"]),
        payout_amount=payout_amount,
        safe_reveals_count=safe_reveals_count,
        idempotency_key=auto_cashout_key,
    )
    _close_mines_round_as_won(
        cursor=cursor,
        round_id=str(round_row["id"]),
        settlement_ledger_transaction_id=str(settlement_result["ledger_transaction_id"]),
        safe_reveals_count=safe_reveals_count,
        revealed_cells=list(round_row["revealed_cells_json"]),
        multiplier_current=Decimal(round_row["multiplier_current"]),
        payout_current=payout_amount,
    )

    return {
        "game_session_id": str(round_row["id"]),
        "status": "won",
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
    settlement_ledger_transaction_id: str,
    safe_reveals_count: int,
    revealed_cells: list[int],
    multiplier_current: Decimal,
    payout_current: Decimal,
) -> None:
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
            round_id,
        ),
    )
    cursor.execute(
        """
        UPDATE platform_rounds
        SET
            status = 'won',
            payout_amount = %s,
            settlement_ledger_transaction_id = %s,
            closed_at = now()
        WHERE id = %s
        """,
        (payout_current, settlement_ledger_transaction_id, round_id),
    )


def _get_access_session_for_update(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    game_code: str | None = None,
) -> dict[str, object] | None:
    query = """
        SELECT
            id,
            user_id,
            game_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        FROM game_access_sessions
        WHERE id = %s
          AND user_id = %s
    """
    params: list[object] = [access_session_id, user_id]
    if game_code is not None:
        query += " AND game_code = %s"
        params.append(game_code)
    query += " FOR UPDATE"
    cursor.execute(query, tuple(params))
    return cursor.fetchone()


def _is_access_session_expired(session: dict[str, object]) -> bool:
    last_activity_at = session["last_activity_at"]
    assert isinstance(last_activity_at, datetime)
    return datetime.now(UTC) - last_activity_at > ACCESS_SESSION_TIMEOUT


def _normalize_access_session_id(access_session_id: str) -> str:
    try:
        return str(UUID(access_session_id))
    except (TypeError, ValueError) as exc:
        raise AccessSessionValidationError("Access session id is not valid") from exc


def _normalize_game_code(game_code: str) -> str:
    normalized_game_code = game_code.strip().lower()
    if not normalized_game_code:
        raise AccessSessionValidationError("Game code is required")
    return normalized_game_code


def _build_timeout_cashout_idempotency_key(
    *,
    user_id: str,
    access_session_id: str,
    round_id: str,
) -> str:
    digest = sha256(f"{access_session_id}:{round_id}".encode("utf-8")).hexdigest()[:32]
    return namespace_mines_round_win_idempotency_key(
        user_id=user_id,
        idempotency_key=f"timeout:{digest}",
    )


def _serialize_access_session(
    row: dict[str, object],
    *,
    auto_cashout: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "game_code": row["game_code"],
        "status": row["status"],
        "started_at": row["started_at"].isoformat(),
        "last_activity_at": row["last_activity_at"].isoformat(),
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "auto_cashout": auto_cashout,
    }
