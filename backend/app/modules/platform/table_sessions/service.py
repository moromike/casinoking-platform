from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

import psycopg

from app.db.connection import db_connection

GAME_CODE_MINES = "mines"
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
TABLE_SESSION_MAX_CHIPS = Decimal("100.000000")
SESSION_STATUS_ACTIVE = "active"
SESSION_STATUS_CLOSED = "closed"
SESSION_STATUS_TIMED_OUT = "timed_out"


class TableSessionValidationError(Exception):
    pass


class TableSessionNotFoundError(Exception):
    pass


class TableSessionStateConflictError(Exception):
    pass


class TableSessionLimitExceededError(Exception):
    pass


def get_table_session_limits(*, user_id: str, wallet_type: str = "cash") -> dict[str, object]:
    normalized_wallet_type = _normalize_wallet_type(wallet_type)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            wallet_row = _get_wallet_for_user(
                cursor=cursor,
                user_id=user_id,
                wallet_type=normalized_wallet_type,
                for_update=False,
            )
            if wallet_row is None:
                available_balance = Decimal("0.000000")
            else:
                available_balance = Decimal(wallet_row["balance_snapshot"]).quantize(
                    Decimal("0.000001")
                )

    max_table_amount = min(available_balance, TABLE_SESSION_MAX_CHIPS).quantize(
        Decimal("0.000001")
    )
    return {
        "game_code": GAME_CODE_MINES,
        "wallet_type": normalized_wallet_type,
        "wallet_balance_available": _format_amount(available_balance),
        "table_session_max_chips": _format_amount(TABLE_SESSION_MAX_CHIPS),
        "default_table_amount": _format_amount(max_table_amount),
        "max_table_amount": _format_amount(max_table_amount),
    }


def create_table_session(
    *,
    user_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
    wallet_type: str,
    table_budget_amount: str,
    access_session_id: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    normalized_wallet_type = _normalize_wallet_type(wallet_type)
    normalized_amount = _parse_amount(table_budget_amount, field_name="table_budget_amount")
    normalized_access_session_id = (
        _normalize_uuid(access_session_id, "Access session id is not valid")
        if access_session_id is not None
        else None
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            table_session = create_table_session_in_transaction(
                cursor=cursor,
                user_id=user_id,
                game_code=normalized_game_code,
                title_code=title_code,
                site_code=site_code,
                wallet_type=normalized_wallet_type,
                table_budget_amount=normalized_amount,
                access_session_id=normalized_access_session_id,
            )

    return table_session


def create_table_session_in_transaction(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_code: str,
    title_code: str | None = None,
    site_code: str | None = None,
    wallet_type: str,
    table_budget_amount: Decimal,
    access_session_id: str | None = None,
) -> dict[str, object]:
    normalized_game_code = _normalize_game_code(game_code)
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    normalized_wallet_type = _normalize_wallet_type(wallet_type)
    if normalized_game_code != GAME_CODE_MINES:
        raise TableSessionValidationError("Game code is not supported")

    _close_orphan_table_sessions_for_user_game(
        cursor=cursor,
        user_id=user_id,
        game_code=normalized_game_code,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
    )

    wallet_row = _get_wallet_for_user(
        cursor=cursor,
        user_id=user_id,
        wallet_type=normalized_wallet_type,
        for_update=True,
    )
    if wallet_row is None:
        raise TableSessionValidationError("Selected wallet is not available")

    if table_budget_amount > TABLE_SESSION_MAX_CHIPS:
        raise TableSessionLimitExceededError("Table session amount exceeds the supported limit")
    if table_budget_amount > wallet_row["balance_snapshot"]:
        raise TableSessionLimitExceededError("Table session amount exceeds available balance")

    if access_session_id is not None:
        _ensure_access_session_matches(
            cursor=cursor,
            user_id=user_id,
            game_code=normalized_game_code,
            title_code=normalized_title_code,
            site_code=normalized_site_code,
            access_session_id=access_session_id,
        )

    table_session_id = str(uuid4())
    cursor.execute(
        """
        INSERT INTO game_table_sessions (
            id,
            access_session_id,
            user_id,
            game_code,
            title_code,
            site_code,
            wallet_account_id,
            wallet_type,
            table_budget_amount,
            table_balance_amount,
            loss_limit_amount,
            loss_reserved_amount,
            loss_consumed_amount,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, %s)
        RETURNING
            id,
            access_session_id,
            user_id,
            game_code,
            title_code,
            site_code,
            wallet_account_id,
            wallet_type,
            table_budget_amount,
            table_balance_amount,
            loss_limit_amount,
            loss_reserved_amount,
            loss_consumed_amount,
            status,
            closed_reason,
            created_at,
            closed_at
        """,
        (
            table_session_id,
            access_session_id,
            user_id,
            normalized_game_code,
            normalized_title_code,
            normalized_site_code,
            wallet_row["id"],
            normalized_wallet_type,
            table_budget_amount,
            table_budget_amount,
            table_budget_amount,
            SESSION_STATUS_ACTIVE,
        ),
    )
    row = cursor.fetchone()
    assert row is not None
    return _serialize_table_session(row)


def get_table_session(*, user_id: str, table_session_id: str) -> dict[str, object]:
    normalized_table_session_id = _normalize_uuid(
        table_session_id,
        "Table session id is not valid",
    )
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = _get_table_session(
                cursor=cursor,
                user_id=user_id,
                table_session_id=normalized_table_session_id,
                for_update=False,
            )
    if row is None:
        raise TableSessionNotFoundError("Table session not found")
    return _serialize_table_session(row)


def close_table_session(*, user_id: str, table_session_id: str) -> dict[str, object]:
    normalized_table_session_id = _normalize_uuid(
        table_session_id,
        "Table session id is not valid",
    )
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = _get_table_session(
                cursor=cursor,
                user_id=user_id,
                table_session_id=normalized_table_session_id,
                for_update=True,
            )
            if row is None:
                raise TableSessionNotFoundError("Table session not found")
            if row["status"] != SESSION_STATUS_ACTIVE:
                return _serialize_table_session(row)
            if row["loss_reserved_amount"] > 0:
                raise TableSessionStateConflictError("Table session has an active round")

            cursor.execute(
                """
                UPDATE game_table_sessions
                SET
                    status = %s,
                    closed_reason = %s,
                    closed_at = now()
                WHERE id = %s
                RETURNING
                    id,
                    access_session_id,
                    user_id,
                    game_code,
                    title_code,
                    site_code,
                    wallet_account_id,
                    wallet_type,
                    table_budget_amount,
                    table_balance_amount,
                    loss_limit_amount,
                    loss_reserved_amount,
                    loss_consumed_amount,
                    status,
                    closed_reason,
                    created_at,
                    closed_at
                """,
                (SESSION_STATUS_CLOSED, "player_closed", normalized_table_session_id),
            )
            closed_row = cursor.fetchone()

    assert closed_row is not None
    return _serialize_table_session(closed_row)


def validate_and_reserve_round_exposure(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    table_session_id: str | None,
    game_code: str,
    wallet_type: str,
    bet_amount: Decimal,
    access_session_id: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_title_code = _normalize_title_code(title_code or TITLE_CODE_MINES_CLASSIC)
    normalized_site_code = _normalize_site_code(site_code or SITE_CODE_CASINOKING)
    if table_session_id is None:
        table_session = create_table_session_in_transaction(
            cursor=cursor,
            user_id=user_id,
            game_code=game_code,
            title_code=normalized_title_code,
            site_code=normalized_site_code,
            wallet_type=wallet_type,
            table_budget_amount=min(TABLE_SESSION_MAX_CHIPS, bet_amount),
            access_session_id=access_session_id,
        )
        normalized_table_session_id = str(table_session["id"])
    else:
        normalized_table_session_id = _normalize_uuid(
            table_session_id,
            "Table session id is not valid",
        )

    row = _get_table_session(
        cursor=cursor,
        user_id=user_id,
        table_session_id=normalized_table_session_id,
        for_update=True,
    )
    if row is None:
        raise TableSessionNotFoundError("Table session not found")
    if row["status"] != SESSION_STATUS_ACTIVE:
        raise TableSessionStateConflictError("Table session is not active")
    if row["game_code"] != _normalize_game_code(game_code):
        raise TableSessionValidationError("Table session game code is not valid")
    if row["title_code"] != normalized_title_code:
        raise TableSessionValidationError("Table session title code is not valid")
    if row["site_code"] != normalized_site_code:
        raise TableSessionValidationError("Table session site code is not valid")
    if row["wallet_type"] != _normalize_wallet_type(wallet_type):
        raise TableSessionValidationError("Table session wallet type is not valid")
    if access_session_id is not None and row["access_session_id"] is not None:
        if str(row["access_session_id"]) != access_session_id:
            raise TableSessionValidationError("Table session access session is not valid")

    table_balance = Decimal(row["table_balance_amount"])
    if table_balance < bet_amount:
        raise TableSessionLimitExceededError("Table session limit exceeded")

    cursor.execute(
        """
        UPDATE game_table_sessions
        SET
            table_balance_amount = table_balance_amount - %s,
            loss_reserved_amount = loss_reserved_amount + %s,
            loss_consumed_amount = GREATEST(
                loss_limit_amount
                - (table_balance_amount - %s)
                - (loss_reserved_amount + %s),
                0
            )
        WHERE id = %s
        RETURNING
            id,
            access_session_id,
            user_id,
            game_code,
            title_code,
            site_code,
            wallet_account_id,
            wallet_type,
            table_budget_amount,
            table_balance_amount,
            loss_limit_amount,
            loss_reserved_amount,
            loss_consumed_amount,
            status,
            closed_reason,
            created_at,
            closed_at
        """,
        (bet_amount, bet_amount, bet_amount, bet_amount, normalized_table_session_id),
    )
    updated_row = cursor.fetchone()
    assert updated_row is not None
    return _serialize_table_session(updated_row)


def consume_reserved_loss(
    *,
    cursor: psycopg.Cursor,
    table_session_id: str | None,
    bet_amount: Decimal,
) -> dict[str, object] | None:
    if table_session_id is None:
        return None
    return _settle_reserved_amount(
        cursor=cursor,
        table_session_id=table_session_id,
        bet_amount=bet_amount,
        consume=True,
    )


def release_reserved_loss(
    *,
    cursor: psycopg.Cursor,
    table_session_id: str | None,
    bet_amount: Decimal,
    payout_amount: Decimal,
) -> dict[str, object] | None:
    if table_session_id is None:
        return None
    return _settle_reserved_amount(
        cursor=cursor,
        table_session_id=table_session_id,
        bet_amount=bet_amount,
        payout_amount=payout_amount,
        consume=False,
    )


def _settle_reserved_amount(
    *,
    cursor: psycopg.Cursor,
    table_session_id: str,
    bet_amount: Decimal,
    consume: bool,
    payout_amount: Decimal = Decimal("0.000000"),
) -> dict[str, object]:
    normalized_table_session_id = _normalize_uuid(
        table_session_id,
        "Table session id is not valid",
    )
    cursor.execute(
        """
        SELECT
            id,
            table_balance_amount,
            loss_limit_amount,
            loss_reserved_amount,
            loss_consumed_amount
        FROM game_table_sessions
        WHERE id = %s
        FOR UPDATE
        """,
        (normalized_table_session_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise TableSessionNotFoundError("Table session not found")
    if row["loss_reserved_amount"] < bet_amount:
        raise TableSessionStateConflictError("Table session reserved amount is not valid")

    if consume:
        cursor.execute(
            """
            UPDATE game_table_sessions
            SET
                loss_reserved_amount = loss_reserved_amount - %s,
                loss_consumed_amount = GREATEST(
                    loss_limit_amount
                    - table_balance_amount
                    - (loss_reserved_amount - %s),
                    0
                )
            WHERE id = %s
            RETURNING
                id,
                access_session_id,
                user_id,
                game_code,
                title_code,
                site_code,
                wallet_account_id,
                wallet_type,
                table_budget_amount,
                table_balance_amount,
                loss_limit_amount,
                loss_reserved_amount,
                loss_consumed_amount,
                status,
                closed_reason,
                created_at,
                closed_at
            """,
            (bet_amount, bet_amount, normalized_table_session_id),
        )
    else:
        cursor.execute(
            """
            UPDATE game_table_sessions
            SET
                table_balance_amount = table_balance_amount + %s,
                loss_reserved_amount = loss_reserved_amount - %s,
                loss_consumed_amount = GREATEST(
                    loss_limit_amount
                    - (table_balance_amount + %s)
                    - (loss_reserved_amount - %s),
                    0
                )
            WHERE id = %s
            RETURNING
                id,
                access_session_id,
                user_id,
                game_code,
                title_code,
                site_code,
                wallet_account_id,
                wallet_type,
                table_budget_amount,
                table_balance_amount,
                loss_limit_amount,
                loss_reserved_amount,
                loss_consumed_amount,
                status,
                closed_reason,
                created_at,
                closed_at
            """,
            (payout_amount, bet_amount, payout_amount, bet_amount, normalized_table_session_id),
        )

    updated_row = cursor.fetchone()
    assert updated_row is not None
    return _serialize_table_session(updated_row)


def _get_wallet_for_user(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    wallet_type: str,
    for_update: bool,
) -> dict[str, object] | None:
    query = """
        SELECT
            wa.id,
            wa.wallet_type,
            wa.balance_snapshot
        FROM wallet_accounts wa
        WHERE wa.user_id = %s
          AND wa.wallet_type = %s
          AND wa.status = 'active'
    """
    if for_update:
        query += " FOR UPDATE"
    cursor.execute(query, (user_id, wallet_type))
    return cursor.fetchone()


def _get_table_session(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    table_session_id: str,
    for_update: bool,
) -> dict[str, object] | None:
    query = """
        SELECT
            id,
            access_session_id,
            user_id,
            game_code,
            title_code,
            site_code,
            wallet_account_id,
            wallet_type,
            table_budget_amount,
            table_balance_amount,
            loss_limit_amount,
            loss_reserved_amount,
            loss_consumed_amount,
            status,
            closed_reason,
            created_at,
            closed_at
        FROM game_table_sessions
        WHERE id = %s
          AND user_id = %s
    """
    if for_update:
        query += " FOR UPDATE"
    cursor.execute(query, (table_session_id, user_id))
    return cursor.fetchone()


def _close_orphan_table_sessions_for_user_game(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_code: str,
    title_code: str,
    site_code: str,
) -> None:
    """Defensive: close any active table_sessions for this user/game before creating a new one.

    The "rigid" invariant requires at most one active table_session per user/game.
    Active rounds should not exist here (gate only shows when no round is active),
    so loss_reserved should be 0; if it isn't, the DB CHECK on closed_at consistency
    will surface the inconsistency.
    """
    cursor.execute(
        """
        UPDATE game_table_sessions
        SET
            status = 'closed',
            closed_reason = 'replaced_by_new_session',
            closed_at = now()
        WHERE user_id = %s
          AND game_code = %s
          AND title_code = %s
          AND site_code = %s
          AND status = 'active'
          AND loss_reserved_amount = 0
        """,
        (user_id, game_code, title_code, site_code),
    )


def _ensure_access_session_matches(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_code: str,
    title_code: str,
    site_code: str,
    access_session_id: str,
) -> None:
    cursor.execute(
        """
        SELECT id
        FROM game_access_sessions
        WHERE id = %s
          AND user_id = %s
          AND game_code = %s
          AND title_code = %s
          AND site_code = %s
          AND status = %s
        """,
        (access_session_id, user_id, game_code, title_code, site_code, SESSION_STATUS_ACTIVE),
    )
    if cursor.fetchone() is None:
        raise TableSessionValidationError("Access session is not active")


def _serialize_table_session(row: dict[str, object]) -> dict[str, object]:
    loss_remaining = (
        Decimal(row["loss_limit_amount"])
        - Decimal(row["loss_reserved_amount"])
        - Decimal(row["loss_consumed_amount"])
    ).quantize(Decimal("0.000001"))
    return {
        "id": str(row["id"]),
        "access_session_id": str(row["access_session_id"]) if row["access_session_id"] else None,
        "game_code": row["game_code"],
        "title_code": row["title_code"],
        "site_code": row["site_code"],
        "wallet_type": row["wallet_type"],
        "table_budget_amount": _format_amount(row["table_budget_amount"]),
        "table_balance_amount": _format_amount(row["table_balance_amount"]),
        "loss_limit_amount": _format_amount(row["loss_limit_amount"]),
        "loss_reserved_amount": _format_amount(row["loss_reserved_amount"]),
        "loss_consumed_amount": _format_amount(row["loss_consumed_amount"]),
        "loss_remaining_amount": _format_amount(loss_remaining),
        "status": row["status"],
        "closed_reason": row["closed_reason"],
        "created_at": row["created_at"].isoformat(),
        "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None,
    }


def _parse_amount(raw_value: str, *, field_name: str) -> Decimal:
    try:
        amount = Decimal(raw_value)
    except (InvalidOperation, TypeError) as exc:
        raise TableSessionValidationError(f"{field_name} is not valid") from exc
    amount = amount.quantize(Decimal("0.000001"))
    if amount <= 0:
        raise TableSessionValidationError(f"{field_name} must be greater than zero")
    return amount


def _normalize_uuid(raw_value: str, message: str) -> str:
    try:
        return str(UUID(str(raw_value)))
    except (TypeError, ValueError) as exc:
        raise TableSessionValidationError(message) from exc


def _normalize_game_code(game_code: str) -> str:
    normalized = game_code.strip().lower()
    if not normalized:
        raise TableSessionValidationError("Game code is required")
    return normalized


def _normalize_title_code(title_code: str) -> str:
    normalized = title_code.strip().lower()
    if not normalized:
        raise TableSessionValidationError("Title code is required")
    return normalized


def _normalize_site_code(site_code: str) -> str:
    normalized = site_code.strip().lower()
    if not normalized:
        raise TableSessionValidationError("Site code is required")
    return normalized


def _normalize_wallet_type(wallet_type: str) -> str:
    normalized = wallet_type.strip().lower()
    if normalized not in {"cash", "bonus"}:
        raise TableSessionValidationError("Wallet type is not valid")
    return normalized


def _format_amount(value: object) -> str:
    return f"{Decimal(value):.6f}"
