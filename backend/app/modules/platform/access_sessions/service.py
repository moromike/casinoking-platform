from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from uuid import UUID, uuid4

import psycopg

from app.core.structured_logging import log_event
from app.db.connection import db_connection
from app.modules.platform.game_codes import (
    GAME_CODE_BOXE,
    GAME_CODE_HI_LO,
    GAME_CODE_MINES,
    is_allowed_game_code,
)
from app.modules.platform.rounds.service import (
    namespace_game_round_win_idempotency_key,
    settle_game_round_win,
)

ACCESS_SESSION_TIMEOUT = timedelta(minutes=3)
ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT = 100
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_CLOSED = "closed"
SESSION_STATUS_TIMED_OUT = "timed_out"

CLOSE_REASON_PLAYER_LOGIN = "player_login_cleanup"
CLOSE_REASON_PLAYER_LOGOUT = "player_logout"
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
            _lock_launchable_title_for_access_session(
                cursor=cursor,
                game_code=normalized_game_code,
                title_code=normalized_title_code,
                site_code=normalized_site_code,
            )
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


def _lock_launchable_title_for_access_session(
    *,
    cursor: psycopg.Cursor,
    game_code: str,
    title_code: str,
    site_code: str,
) -> None:
    cursor.execute(
        """
        SELECT
            gt.status AS title_status,
            gt.archived_at,
            gt.is_master,
            ge.status AS engine_status,
            s.status AS site_status,
            st.status AS site_title_status,
            st.lobby_visibility,
            st.real_enabled
        FROM site_titles st
        JOIN sites s ON s.site_code = st.site_code
        JOIN game_titles gt ON gt.title_code = st.title_code
        JOIN game_engines ge ON ge.engine_code = gt.engine_code
        WHERE st.site_code = %s
          AND st.title_code = %s
          AND gt.engine_code = %s
        FOR UPDATE OF gt
        """,
        (site_code, title_code, game_code),
    )
    row = cursor.fetchone()
    if row is None:
        raise AccessSessionValidationError("Title is not published on this site")
    if row["site_status"] != "active":
        raise AccessSessionValidationError("Site is not active")
    if row["engine_status"] != "active":
        raise AccessSessionValidationError("Engine is not active")
    if row["title_status"] != "active" or row["archived_at"] is not None:
        raise AccessSessionValidationError("Title is not active")
    if row["is_master"] is True:
        raise AccessSessionValidationError("Master titles cannot be launched publicly")
    if row["site_title_status"] != "active" or row["lobby_visibility"] != "visible":
        raise AccessSessionValidationError("Title is not visible in the player library")
    if row["real_enabled"] is not True:
        raise AccessSessionValidationError("Real launch mode is not enabled for this title")


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


def timeout_expired_access_sessions(
    *,
    limit: int = ACCESS_SESSION_TIMEOUT_SWEEP_LIMIT,
    job_id: str | None = None,
) -> int:
    cutoff = datetime.now(UTC) - ACCESS_SESSION_TIMEOUT
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
                    status,
                    closed_reason
                FROM game_access_sessions
                WHERE status = %s
                  AND last_activity_at < %s
                ORDER BY last_activity_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT %s
                """,
                (SESSION_STATUS_ACTIVE, cutoff, limit),
            )
            rows = cursor.fetchall() or []
            for session in rows:
                _timeout_access_session(cursor=cursor, session=session, job_id=job_id)
            return len(rows)


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
            closed_session, auto_cashout = _close_access_session_in_transaction(
                cursor=cursor,
                access_session_id=normalized_session_id,
                user_id=user_id,
                reason=CLOSE_REASON_ACCESS_CLOSED,
            )

    if closed_session is None:
        raise AccessSessionNotFoundError("Access session not found")
    return _serialize_access_session(closed_session, auto_cashout=auto_cashout)


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

    auto_cashout = _auto_settle_active_round_for_access_session(
        cursor=cursor,
        session=session,
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
    job_id: str | None = None,
) -> tuple[dict[str, object], dict[str, object] | None]:
    try:
        auto_cashout = _auto_settle_active_round_for_access_session(
            cursor=cursor,
            session=session,
        )
    except Exception as exc:
        log_event(
            "critical",
            "access_session.auto_settlement_failed",
            {
                "access_session_id": str(session["id"]),
                "game_code": str(session["game_code"]),
                "title_code": str(session["title_code"]),
                "error_code": "CK.SYSTEM.SERVICE_UNAVAILABLE",
                "exception_type": type(exc).__name__,
            },
            job_id=job_id,
        )
        raise

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


def _auto_settle_active_round_for_access_session(
    *,
    cursor: psycopg.Cursor,
    session: dict[str, object],
) -> dict[str, object] | None:
    game_code = str(session["game_code"])
    access_session_id = str(session["id"])
    user_id = str(session["user_id"])
    handler = _AUTO_SETTLE_ACTIVE_ROUND_HANDLERS.get(game_code)
    if handler is None:
        return None
    return handler(
        cursor=cursor,
        access_session_id=access_session_id,
        user_id=user_id,
    )


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

    auto_cashout_key = _build_timeout_cashout_idempotency_key(
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

    auto_cashout_key = _build_timeout_cashout_idempotency_key(
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

    auto_cashout_key = _build_timeout_cashout_idempotency_key(
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


_AUTO_SETTLE_ACTIVE_ROUND_HANDLERS = {
    GAME_CODE_MINES: _auto_cashout_active_mines_round,
    GAME_CODE_BOXE: _auto_cashout_active_boxe_round,
    GAME_CODE_HI_LO: _auto_cashout_active_hi_lo_round,
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


def _close_mines_round_as_won(
    *,
    cursor: psycopg.Cursor,
    round_id: str,
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
    if not is_allowed_game_code(normalized_game_code):
        raise AccessSessionValidationError("Game code is not supported")
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
    game_code: str,
    user_id: str,
    access_session_id: str,
    round_id: str,
) -> str:
    digest = sha256(f"{access_session_id}:{round_id}".encode("utf-8")).hexdigest()[:32]
    return namespace_game_round_win_idempotency_key(
        game_code=game_code,
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
