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
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_CLOSED = "closed"
SESSION_STATUS_TIMED_OUT = "timed_out"

CLOSE_REASON_PLAYER_EXIT = "player_exit"
CLOSE_REASON_PLAYER_LOGIN = "player_login_cleanup"
CLOSE_REASON_PLAYER_LOGOUT = "player_logout"
CLOSE_REASON_NEW_SESSION = "replaced_by_new_session"
CLOSE_REASON_ACCESS_TIMEOUT = "access_session_timeout"
CLOSE_REASON_ACCESS_CLOSED = "access_session_closed"
CLOSE_REASON_ADMIN_VOIDED = "admin_voided"


class AccessSessionValidationError(Exception):
    pass


class AccessSessionNotFoundError(Exception):
    pass


class AccessSessionStateConflictError(Exception):
    pass


class AccessSessionVoidedByOperatorError(Exception):
    """Raised when a player operation hits an access_session that was
    closed by an admin force-close (closed_reason='admin_voided').
    The frontend uses this to show a neutral 'Sessione terminata' overlay.
    """
    pass


def create_access_session(
    *,
    user_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                FROM game_access_sessions
                WHERE user_id = %s
                  AND game_code = %s
                  AND title_code = %s
                  AND site_code = %s
                  AND status = %s
                ORDER BY started_at DESC
                LIMIT 1
                FOR UPDATE
                """,
                (
                    user_id,
                    normalized_game_code,
                    normalized_title_code,
                    normalized_site_code,
                    SESSION_STATUS_ACTIVE,
                ),
            )
            existing = cursor.fetchone()
            if existing is not None:
                if _is_access_session_expired(existing):
                    _timeout_access_session(cursor=cursor, session=existing)
                else:
                    return _serialize_access_session(existing)

            access_session_id = str(uuid4())
            cursor.execute(
                """
                INSERT INTO game_access_sessions (
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, now(), now(), %s)
                RETURNING
                    id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    started_at,
                    last_activity_at,
                    ended_at,
                    status
                """,
                (
                    access_session_id,
                    user_id,
                    normalized_game_code,
                    normalized_title_code,
                    normalized_site_code,
                    SESSION_STATUS_ACTIVE,
                ),
            )
            row = cursor.fetchone()

    assert row is not None
    return _serialize_access_session(row)


def force_close_user_sessions(
    *,
    user_id: str,
    game_code: str | None = None,
    reason: str,
) -> dict[str, object]:
    """Close all active access_sessions and table_sessions for a user.

    If game_code is None, applies to all games.
    Cascades through close_access_session, which auto-settles active rounds
    and closes linked table_sessions.
    """
    normalized_game_code = _normalize_game_code(game_code) if game_code else None
    closed_count = 0
    with db_connection() as connection:
        with connection.cursor() as cursor:
            closed_count = _force_close_user_sessions_in_transaction(
                cursor=cursor,
                user_id=user_id,
                game_code=normalized_game_code,
                reason=reason,
            )

    return {"closed_sessions": closed_count, "reason": reason}


def _force_close_user_sessions_in_transaction(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_code: str | None,
    reason: str,
) -> int:
    query = """
        SELECT id, game_code
        FROM game_access_sessions
        WHERE user_id = %s
          AND status = %s
    """
    params: list[object] = [user_id, SESSION_STATUS_ACTIVE]
    if game_code is not None:
        query += " AND game_code = %s"
        params.append(game_code)
    query += " FOR UPDATE"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall() or []

    closed_count = 0
    for row in rows:
        closed_session, _ = _close_access_session_in_transaction(
            cursor=cursor,
            access_session_id=str(row["id"]),
            user_id=user_id,
            reason=reason,
        )
        if closed_session is not None and closed_session["status"] == SESSION_STATUS_CLOSED:
            closed_count += 1

    # Sweep any orphan active table_sessions not linked to an access_session.
    sweep_query = """
        UPDATE game_table_sessions
        SET
            status = %s,
            closed_reason = %s,
            closed_at = now()
        WHERE status = %s
          AND user_id = %s
    """
    sweep_params: list[object] = [
        SESSION_STATUS_CLOSED,
        reason,
        SESSION_STATUS_ACTIVE,
        user_id,
    ]
    if game_code is not None:
        sweep_query += " AND game_code = %s"
        sweep_params.append(game_code)
    cursor.execute(sweep_query, tuple(sweep_params))

    return closed_count


def ping_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    conflict_message: str | None = None
    voided_by_operator = False

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

            if (
                conflict_message is None
                and session["status"] != SESSION_STATUS_ACTIVE
                and session.get("closed_reason") == CLOSE_REASON_ADMIN_VOIDED
            ):
                voided_by_operator = True

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
                        title_code,
                        site_code,
                        started_at,
                        last_activity_at,
                        ended_at,
                        status
                    """,
                    (normalized_session_id,),
                )
                updated_session = cursor.fetchone()

    if voided_by_operator:
        raise AccessSessionVoidedByOperatorError(
            "Access session was closed by an operator"
        )

    if conflict_message is not None:
        raise AccessSessionStateConflictError(conflict_message)

    assert updated_session is not None
    return _serialize_access_session(updated_session)


def close_access_session(*, user_id: str, access_session_id: str) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)

    with db_connection() as connection:
        with connection.cursor() as cursor:
            closed_session, _ = _close_access_session_in_transaction(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                reason=CLOSE_REASON_ACCESS_CLOSED,
            )

    if closed_session is None:
        raise AccessSessionNotFoundError("Access session not found")
    return _serialize_access_session(closed_session)


def _close_access_session_in_transaction(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    reason: str,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    session = _get_access_session_for_update(
        cursor=cursor,
        access_session_id=access_session_id,
        user_id=user_id,
    )
    if session is None:
        return None, None

    if session["status"] != SESSION_STATUS_ACTIVE:
        return session, None

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
            last_activity_at = now(),
            ended_at = now(),
            status = %s,
            closed_reason = %s
        WHERE id = %s
        RETURNING
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        """,
        (SESSION_STATUS_CLOSED, reason, access_session_id),
    )
    closed_session = cursor.fetchone()

    _close_table_sessions_for_access_session(
        cursor=cursor,
        access_session_id=access_session_id,
        user_id=str(session["user_id"]),
        game_code=str(session["game_code"]),
        title_code=str(session["title_code"]),
        site_code=str(session["site_code"]),
        reason=reason,
    )

    return closed_session, auto_cashout


def ensure_access_session_active_for_round_start(
    *,
    user_id: str,
    access_session_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_session_id = _normalize_access_session_id(access_session_id)
    normalized_game_code = _normalize_game_code(game_code)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    timed_out = False

    with db_connection() as connection:
        with connection.cursor() as cursor:
            session = _get_access_session_for_update(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                game_code=normalized_game_code,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
            )
            if session is None:
                raise AccessSessionNotFoundError("Access session not found")

            if (
                session["status"] != SESSION_STATUS_ACTIVE
                and session.get("closed_reason") == CLOSE_REASON_ADMIN_VOIDED
            ):
                raise AccessSessionVoidedByOperatorError(
                    "Access session was closed by an operator"
                )

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
                        title_code,
                        site_code,
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
            status = %s,
            closed_reason = %s
        WHERE id = %s
        RETURNING
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status
        """,
        (SESSION_STATUS_TIMED_OUT, CLOSE_REASON_ACCESS_TIMEOUT, str(session["id"])),
    )
    timed_out_session = cursor.fetchone()
    assert timed_out_session is not None

    _close_table_sessions_for_access_session(
        cursor=cursor,
        access_session_id=str(session["id"]),
        user_id=str(session["user_id"]),
        game_code=str(session["game_code"]),
        title_code=str(session["title_code"]),
        site_code=str(session["site_code"]),
        reason=CLOSE_REASON_ACCESS_TIMEOUT,
    )

    return timed_out_session, auto_cashout


def _close_table_sessions_for_access_session(
    *,
    cursor: psycopg.Cursor,
    access_session_id: str,
    user_id: str,
    game_code: str,
    title_code: str,
    site_code: str,
    reason: str,
) -> None:
    """Close all active table_sessions linked to this access_session,
    plus any orphan active table_sessions for the same user/game.
    Auto-cashout has already happened upstream, so loss_reserved should be 0.
    """
    cursor.execute(
        """
        UPDATE game_table_sessions
        SET
            status = %s,
            closed_reason = %s,
            closed_at = now()
        WHERE status = %s
          AND user_id = %s
          AND game_code = %s
          AND title_code = %s
          AND site_code = %s
          AND (access_session_id = %s OR access_session_id IS NULL)
        """,
        (
            SESSION_STATUS_CLOSED,
            reason,
            SESSION_STATUS_ACTIVE,
            user_id,
            game_code,
            title_code,
            site_code,
            access_session_id,
        ),
    )


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
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object] | None:
    query = """
        SELECT
            id,
            user_id,
            game_code,
            title_code,
            site_code,
            started_at,
            last_activity_at,
            ended_at,
            status,
            closed_reason
        FROM game_access_sessions
        WHERE id = %s
          AND user_id = %s
    """
    params: list[object] = [access_session_id, user_id]
    if game_code is not None:
        query += " AND game_code = %s"
        params.append(game_code)
    if title_code is not None:
        query += " AND title_code = %s"
        params.append(title_code)
    if site_code is not None:
        query += " AND site_code = %s"
        params.append(site_code)
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


def _normalize_title_code(title_code: str) -> str:
    normalized_title_code = title_code.strip().lower()
    if not normalized_title_code:
        raise AccessSessionValidationError("Title code is required")
    return normalized_title_code


def _normalize_site_code(site_code: str) -> str:
    normalized_site_code = site_code.strip().lower()
    if not normalized_site_code:
        raise AccessSessionValidationError("Site code is required")
    return normalized_site_code


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
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "status": row["status"],
        "started_at": row["started_at"].isoformat(),
        "last_activity_at": row["last_activity_at"].isoformat(),
        "ended_at": row["ended_at"].isoformat() if row["ended_at"] else None,
        "auto_cashout": auto_cashout,
    }
