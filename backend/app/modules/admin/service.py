from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection
from app.modules.auth.service import (
    AuthConflictError,
    AuthForbiddenError,
    AuthInvalidCredentialsError,
    AuthValidationError,
    change_password,
)
from app.modules.auth.security import hash_password

ACTION_TYPE_ADMIN_ADJUSTMENT = "admin_adjustment"
ACTION_TYPE_BONUS_GRANT = "bonus_grant"
CHIP_CURRENCY = "CHIP"
DIRECTION_CREDIT = "credit"
DIRECTION_DEBIT = "debit"
GAME_PNL_MINES_ACCOUNT_CODE = "GAME_PNL_MINES"
HOUSE_BONUS_ACCOUNT_CODE = "HOUSE_BONUS"
HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
PROMO_RESERVE_ACCOUNT_CODE = "PROMO_RESERVE"
WALLET_TYPE_BONUS = "bonus"
WALLET_TYPE_CASH = "cash"
FINANCIAL_REPORT_ACCOUNT_CODES = (
    HOUSE_CASH_ACCOUNT_CODE,
    HOUSE_BONUS_ACCOUNT_CODE,
    GAME_PNL_MINES_ACCOUNT_CODE,
    PROMO_RESERVE_ACCOUNT_CODE,
)


class AdminValidationError(Exception):
    pass


class AdminNotFoundError(Exception):
    pass


class AdminIdempotencyConflictError(Exception):
    pass


class AdminInsufficientBalanceError(Exception):
    pass


def change_admin_password(
    *,
    admin_id: str,
    old_password: str,
    new_password: str,
) -> dict[str, object]:
    """Change the password of an authenticated admin account.

    Delegates to the shared auth service change_password with required_role="admin".
    Raises AuthValidationError, AuthInvalidCredentialsError, or AuthForbiddenError
    on failure — callers must handle these.
    """
    return change_password(
        user_id=admin_id,
        old_password=old_password,
        new_password=new_password,
        required_role="admin",
    )


def suspend_user_for_admin(
    *,
    admin_user_id: str,
    target_user_id: str,
) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_user_exists(cursor=cursor, user_id=admin_user_id, label="Admin user")
            cursor.execute(
                """
                SELECT id, email, role, status, created_at
                FROM users
                WHERE id = %s
                FOR UPDATE
                """,
                (target_user_id,),
            )
            user_row = cursor.fetchone()
            if user_row is None:
                raise AdminNotFoundError("Target user not found")

            if user_row["status"] != "suspended":
                cursor.execute(
                    """
                    UPDATE users
                    SET status = 'suspended'
                    WHERE id = %s
                    """,
                    (target_user_id,),
                )

    return {
        "target_user_id": str(user_row["id"]),
        "email": user_row["email"],
        "role": user_row["role"],
        "status": "suspended",
        "created_at": user_row["created_at"].isoformat(),
    }


def list_users_for_admin(*, email_query: str | None = None) -> list[dict[str, object]]:
    normalized_query = email_query.strip().lower() if email_query else None

    with db_connection() as connection:
        with connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT
                        u.id,
                        u.email,
                        u.role,
                        u.status,
                        u.created_at,
                        ap.is_superadmin,
                        ap.areas
                    FROM users u
                    LEFT JOIN admin_profiles ap ON ap.user_id = u.id
                    WHERE u.email ILIKE %s
                    ORDER BY u.created_at DESC
                    LIMIT 100
                    """,
                    (f"%{normalized_query}%",),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        u.id,
                        u.email,
                        u.role,
                        u.status,
                        u.created_at,
                        ap.is_superadmin,
                        ap.areas
                    FROM users u
                    LEFT JOIN admin_profiles ap ON ap.user_id = u.id
                    ORDER BY u.created_at DESC
                    LIMIT 100
                    """
                )
            rows = cursor.fetchall()

    return [
        {
            "id": str(row["id"]),
            "email": row["email"],
            "role": row["role"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
            "is_superadmin": bool(row["is_superadmin"]) if row["is_superadmin"] is not None else None,
            "areas": list(row["areas"]) if row["areas"] is not None else None,
        }
        for row in rows
    ]


def get_admin_profile(*, user_id: str) -> dict[str, object] | None:
    """Return admin profile (is_superadmin, areas) for a given user_id, or None if not found."""
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, is_superadmin, areas, created_at
                FROM admin_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "user_id": str(row["user_id"]),
        "is_superadmin": bool(row["is_superadmin"]),
        "areas": list(row["areas"]),
        "created_at": row["created_at"].isoformat(),
    }


def create_admin_user(
    *,
    email: str,
    password: str,
    is_superadmin: bool,
    areas: list[str],
) -> dict[str, object]:
    """Create a new admin user with the given profile.

    Admin users do not receive wallet/ledger bootstrap (that is for players only).
    Raises AdminValidationError on bad input, AuthConflictError if email already exists.
    """
    normalized_email = email.strip().lower()
    if "@" not in normalized_email or "." not in normalized_email:
        raise AdminValidationError("Email is not valid")
    if len(password) < 8:
        raise AdminValidationError("Password must be at least 8 characters long")

    normalized_areas = [a.strip().lower() for a in areas if a.strip()]
    valid_areas = {"finance", "end_user", "mines"}
    for area in normalized_areas:
        if area not in valid_areas:
            raise AdminValidationError(
                f"Invalid area: {area}. Must be one of: {', '.join(sorted(valid_areas))}"
            )

    password_hash = hash_password(password)
    user_id = str(uuid4())

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (id, email, role, status)
                    VALUES (%s, %s, 'admin', 'active')
                    """,
                    (user_id, normalized_email),
                )
                cursor.execute(
                    """
                    INSERT INTO user_credentials (user_id, password_hash)
                    VALUES (%s, %s)
                    """,
                    (user_id, password_hash),
                )
                cursor.execute(
                    """
                    INSERT INTO admin_profiles (user_id, is_superadmin, areas)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                        SET is_superadmin = EXCLUDED.is_superadmin,
                            areas = EXCLUDED.areas
                    """,
                    (user_id, is_superadmin, normalized_areas),
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name == "users_email_key":
            raise AuthConflictError("Email already registered") from exc
        raise

    return {
        "user_id": user_id,
        "email": normalized_email,
        "role": "admin",
        "status": "active",
        "is_superadmin": is_superadmin,
        "areas": normalized_areas,
    }


def update_admin_profile(
    *,
    user_id: str,
    is_superadmin: bool,
    areas: list[str],
) -> dict[str, object]:
    """Update is_superadmin and areas for an existing admin user."""
    normalized_areas = [a.strip().lower() for a in areas if a.strip()]
    valid_areas = {"finance", "end_user", "mines"}
    for area in normalized_areas:
        if area not in valid_areas:
            raise AdminValidationError(f"Invalid area: {area}. Must be one of: {', '.join(sorted(valid_areas))}")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM users WHERE id = %s AND role = 'admin'
                """,
                (user_id,),
            )
            if cursor.fetchone() is None:
                raise AdminNotFoundError("Admin user not found")

            cursor.execute(
                """
                INSERT INTO admin_profiles (user_id, is_superadmin, areas)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                    SET is_superadmin = EXCLUDED.is_superadmin,
                        areas = EXCLUDED.areas
                """,
                (user_id, is_superadmin, normalized_areas),
            )

    return {
        "user_id": user_id,
        "is_superadmin": is_superadmin,
        "areas": normalized_areas,
    }


def get_ledger_report_for_admin() -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    lt.id,
                    lt.user_id,
                    u.email AS user_email,
                    lt.transaction_type,
                    lt.reference_type,
                    lt.reference_id,
                    lt.idempotency_key,
                    lt.created_at,
                    COUNT(le.id) AS entry_count,
                    COALESCE(
                        SUM(CASE WHEN le.entry_side = 'debit' THEN le.amount ELSE 0 END),
                        0
                    ) AS total_debit,
                    COALESCE(
                        SUM(CASE WHEN le.entry_side = 'credit' THEN le.amount ELSE 0 END),
                        0
                    ) AS total_credit
                FROM ledger_transactions lt
                LEFT JOIN users u ON u.id = lt.user_id
                LEFT JOIN ledger_entries le ON le.transaction_id = lt.id
                GROUP BY
                    lt.id,
                    lt.user_id,
                    u.email,
                    lt.transaction_type,
                    lt.reference_type,
                    lt.reference_id,
                    lt.idempotency_key,
                    lt.created_at
                ORDER BY lt.created_at DESC
                LIMIT 100
                """
            )
            transaction_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    wa.id AS wallet_account_id,
                    wa.user_id,
                    u.email AS user_email,
                    wa.wallet_type,
                    wa.currency_code,
                    wa.balance_snapshot,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN le.entry_side = 'credit' THEN le.amount
                                ELSE -le.amount
                            END
                        ),
                        0
                    ) AS ledger_balance,
                    wa.balance_snapshot - COALESCE(
                        SUM(
                            CASE
                                WHEN le.entry_side = 'credit' THEN le.amount
                                ELSE -le.amount
                            END
                        ),
                        0
                    ) AS drift
                FROM wallet_accounts wa
                JOIN users u ON u.id = wa.user_id
                JOIN ledger_accounts la ON la.id = wa.ledger_account_id
                LEFT JOIN ledger_entries le ON le.ledger_account_id = la.id
                GROUP BY
                    wa.id,
                    wa.user_id,
                    u.email,
                    wa.wallet_type,
                    wa.currency_code,
                    wa.balance_snapshot
                ORDER BY ABS(
                    wa.balance_snapshot - COALESCE(
                        SUM(
                            CASE
                                WHEN le.entry_side = 'credit' THEN le.amount
                                ELSE -le.amount
                            END
                        ),
                        0
                    )
                ) DESC, u.email, wa.wallet_type
                """
            )
            reconciliation_rows = cursor.fetchall()

    return {
        "summary": {
            "recent_transaction_count": len(transaction_rows),
            "balanced_transaction_count": sum(
                1
                for row in transaction_rows
                if row["total_debit"] == row["total_credit"]
            ),
            "wallet_count": len(reconciliation_rows),
            "wallets_with_drift_count": sum(
                1
                for row in reconciliation_rows
                if _format_amount(row["drift"]) != "0.000000"
            ),
        },
        "recent_transactions": [
            {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]) if row["user_id"] else None,
                "user_email": row["user_email"],
                "transaction_type": row["transaction_type"],
                "reference_type": row["reference_type"],
                "reference_id": str(row["reference_id"]) if row["reference_id"] else None,
                "idempotency_key": row["idempotency_key"],
                "entry_count": row["entry_count"],
                "total_debit": _format_amount(row["total_debit"]),
                "total_credit": _format_amount(row["total_credit"]),
                "created_at": row["created_at"].isoformat(),
            }
            for row in transaction_rows
        ],
        "wallet_reconciliation": [
            {
                "wallet_account_id": str(row["wallet_account_id"]),
                "user_id": str(row["user_id"]),
                "user_email": row["user_email"],
                "wallet_type": row["wallet_type"],
                "currency_code": row["currency_code"],
                "balance_snapshot": _format_amount(row["balance_snapshot"]),
                "ledger_balance": _format_amount(row["ledger_balance"]),
                "drift": _format_amount(row["drift"]),
            }
            for row in reconciliation_rows
        ],
    }


def get_financial_sessions_report(
    *,
    user_id: str | None = None,
    email_query: str | None = None,
    wallet_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    include_legacy: bool = True,
) -> dict[str, object]:
    normalized_wallet_type = _parse_wallet_type(wallet_type) if wallet_type is not None else None
    normalized_email_query = email_query.strip().lower() if email_query else None
    parsed_date_from = _parse_report_datetime(
        date_from,
        field_name="date_from",
        end_of_day=False,
    )
    parsed_date_to = _parse_report_datetime(
        date_to,
        field_name="date_to",
        end_of_day=True,
    )
    if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
        raise AdminValidationError("date_from must be earlier than or equal to date_to")

    transaction_rows = _fetch_financial_transaction_rows(
        user_id=user_id,
        email_query=normalized_email_query,
        wallet_type=normalized_wallet_type,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
    )

    sessions_by_id: dict[str, dict[str, object]] = {}
    total_bank_delta = Decimal("0.000000")

    for row in transaction_rows:
        session_id, is_legacy = _build_financial_session_identity(row)
        if is_legacy and not include_legacy:
            continue

        session = sessions_by_id.get(session_id)
        if session is None:
            session = {
                "session_id": session_id,
                "is_legacy": is_legacy,
                "user_id": str(row["user_id"]),
                "user_email": row["user_email"],
                "game_code": row["game_code"],
                "started_at": _serialize_session_started_at(row, is_legacy=is_legacy),
                "ended_at": _serialize_session_ended_at(row, is_legacy=is_legacy),
                "status": row["access_session_status"] if not is_legacy else "closed",
                "total_transactions": 0,
                "bank_total_credit_decimal": Decimal("0.000000"),
                "bank_total_debit_decimal": Decimal("0.000000"),
            }
            sessions_by_id[session_id] = session

        session["total_transactions"] = int(session["total_transactions"]) + 1
        session["bank_total_credit_decimal"] = (
            Decimal(session["bank_total_credit_decimal"]) + row["bank_total_credit"]
        )
        session["bank_total_debit_decimal"] = (
            Decimal(session["bank_total_debit_decimal"]) + row["bank_total_debit"]
        )

        if is_legacy:
            current_started_at = str(session["started_at"])
            current_ended_at = str(session["ended_at"])
            candidate_started_at = row["transaction_created_at"].isoformat()
            candidate_ended_at = row["transaction_created_at"].isoformat()
            if candidate_started_at < current_started_at:
                session["started_at"] = candidate_started_at
            if candidate_ended_at > current_ended_at:
                session["ended_at"] = candidate_ended_at

    sessions: list[dict[str, object]] = []
    for session in sessions_by_id.values():
        bank_total_credit = Decimal(session.pop("bank_total_credit_decimal"))
        bank_total_debit = Decimal(session.pop("bank_total_debit_decimal"))
        bank_delta = bank_total_credit - bank_total_debit
        total_bank_delta += bank_delta
        sessions.append(
            {
                **session,
                "bank_total_credit": _format_amount(bank_total_credit),
                "bank_total_debit": _format_amount(bank_total_debit),
                "bank_delta": _format_amount(bank_delta),
            }
        )

    sessions.sort(key=lambda item: str(item["started_at"]), reverse=True)

    return {
        "sessions": sessions,
        "summary": {
            "total_bank_delta_period": _format_amount(total_bank_delta),
        },
    }


def get_financial_session_detail(*, session_id: str) -> dict[str, object]:
    transaction_rows = _fetch_financial_transaction_rows_for_session(session_id=session_id)
    if not transaction_rows:
        raise AdminNotFoundError("Financial session not found")

    first_row = transaction_rows[0]
    resolved_session_id, is_legacy = _build_financial_session_identity(first_row)
    events: list[dict[str, object]] = []
    bank_total_credit = Decimal("0.000000")
    bank_total_debit = Decimal("0.000000")
    legacy_started_at = first_row["transaction_created_at"].isoformat()
    legacy_ended_at = first_row["transaction_created_at"].isoformat()
    latest_transaction_timestamp = first_row["transaction_created_at"]

    for row in transaction_rows:
        event_credit = row["bank_total_credit"]
        event_debit = row["bank_total_debit"]
        event_delta = event_credit - event_debit
        bank_total_credit += event_credit
        bank_total_debit += event_debit
        if row["transaction_created_at"] > latest_transaction_timestamp:
            latest_transaction_timestamp = row["transaction_created_at"]
        if is_legacy:
            candidate_timestamp = row["transaction_created_at"].isoformat()
            if candidate_timestamp < legacy_started_at:
                legacy_started_at = candidate_timestamp
            if candidate_timestamp > legacy_ended_at:
                legacy_ended_at = candidate_timestamp
        events.append(
            {
                "ledger_transaction_id": str(row["ledger_transaction_id"]),
                "platform_round_id": str(row["round_id"]),
                "timestamp": row["transaction_created_at"].isoformat(),
                "transaction_type": row["transaction_type"],
                "wallet_type": row["wallet_type"],
                "bank_credit": _format_amount(event_credit),
                "bank_debit": _format_amount(event_debit),
                "delta": _format_amount(event_delta),
                "game_enrichment": _build_game_enrichment(row),
            }
        )

    bank_delta = bank_total_credit - bank_total_debit
    return {
        "session_id": resolved_session_id,
        "is_legacy": is_legacy,
        "user_id": str(first_row["user_id"]),
        "user_email": first_row["user_email"],
        "game_code": first_row["game_code"],
        "started_at": (
            legacy_started_at
            if is_legacy
            else _serialize_session_started_at(first_row, is_legacy=False)
        ),
        "ended_at": (
            legacy_ended_at
            if is_legacy
            else (
                first_row["access_session_ended_at"].isoformat()
                if first_row["access_session_ended_at"]
                else latest_transaction_timestamp.isoformat()
            )
        ),
        "status": first_row["access_session_status"] if not is_legacy else "closed",
        "bank_total_credit": _format_amount(bank_total_credit),
        "bank_total_debit": _format_amount(bank_total_debit),
        "bank_delta": _format_amount(bank_delta),
        "events": events,
    }


def create_bonus_grant(
    *,
    admin_user_id: str,
    target_user_id: str,
    idempotency_key: str,
    amount: str,
    reason: str,
) -> dict[str, object]:
    amount_decimal = _parse_amount(amount)
    normalized_reason = _parse_reason(reason)
    request_fingerprint = _build_request_fingerprint(
        action_type=ACTION_TYPE_BONUS_GRANT,
        target_user_id=target_user_id,
        wallet_type=WALLET_TYPE_BONUS,
        direction=DIRECTION_CREDIT,
        amount=amount_decimal,
        reason=normalized_reason,
    )
    namespaced_idempotency_key = _build_storage_idempotency_key(
        scope="admin:bonus_grant",
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        client_idempotency_key=idempotency_key,
    )

    return _apply_admin_wallet_action(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        action_type=ACTION_TYPE_BONUS_GRANT,
        wallet_type=WALLET_TYPE_BONUS,
        direction=DIRECTION_CREDIT,
        amount_decimal=amount_decimal,
        reason=normalized_reason,
        counterparty_account_code=PROMO_RESERVE_ACCOUNT_CODE,
        namespaced_idempotency_key=namespaced_idempotency_key,
        request_fingerprint=request_fingerprint,
    )


def create_wallet_adjustment(
    *,
    admin_user_id: str,
    target_user_id: str,
    idempotency_key: str,
    wallet_type: str,
    direction: str,
    amount: str,
    reason: str,
) -> dict[str, object]:
    normalized_wallet_type = _parse_wallet_type(wallet_type)
    normalized_direction = _parse_direction(direction)
    amount_decimal = _parse_amount(amount)
    normalized_reason = _parse_reason(reason)
    request_fingerprint = _build_request_fingerprint(
        action_type=ACTION_TYPE_ADMIN_ADJUSTMENT,
        target_user_id=target_user_id,
        wallet_type=normalized_wallet_type,
        direction=normalized_direction,
        amount=amount_decimal,
        reason=normalized_reason,
    )
    namespaced_idempotency_key = _build_storage_idempotency_key(
        scope="admin:adjustment",
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        client_idempotency_key=idempotency_key,
    )

    counterparty_account_code = (
        HOUSE_CASH_ACCOUNT_CODE
        if normalized_wallet_type == WALLET_TYPE_CASH
        else HOUSE_BONUS_ACCOUNT_CODE
    )

    return _apply_admin_wallet_action(
        admin_user_id=admin_user_id,
        target_user_id=target_user_id,
        action_type=ACTION_TYPE_ADMIN_ADJUSTMENT,
        wallet_type=normalized_wallet_type,
        direction=normalized_direction,
        amount_decimal=amount_decimal,
        reason=normalized_reason,
        counterparty_account_code=counterparty_account_code,
        namespaced_idempotency_key=namespaced_idempotency_key,
        request_fingerprint=request_fingerprint,
    )


def _apply_admin_wallet_action(
    *,
    admin_user_id: str,
    target_user_id: str,
    action_type: str,
    wallet_type: str,
    direction: str,
    amount_decimal: Decimal,
    reason: str,
    counterparty_account_code: str,
    namespaced_idempotency_key: str,
    request_fingerprint: str,
) -> dict[str, object]:
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_action = _get_existing_action_by_idempotency(
                    cursor=cursor,
                    idempotency_key=namespaced_idempotency_key,
                )
                if existing_action is not None:
                    if existing_action["request_fingerprint"] != request_fingerprint:
                        raise AdminIdempotencyConflictError(
                            "Idempotency key already used with a different payload"
                        )
                    return _response_from_existing(existing_action)

                _ensure_user_exists(cursor=cursor, user_id=admin_user_id, label="Admin user")
                _ensure_user_exists(cursor=cursor, user_id=target_user_id, label="Target user")

                cursor.execute(
                    """
                    SELECT
                        wa.id,
                        wa.balance_snapshot,
                        wa.wallet_type,
                        la.id AS ledger_account_id,
                        la.account_code AS player_account_code
                    FROM wallet_accounts wa
                    JOIN ledger_accounts la ON la.id = wa.ledger_account_id
                    WHERE wa.user_id = %s
                      AND wa.wallet_type = %s
                      AND wa.status = 'active'
                    FOR UPDATE
                    """,
                    (target_user_id, wallet_type),
                )
                wallet_row = cursor.fetchone()
                if wallet_row is None:
                    raise AdminNotFoundError("Target wallet not found")

                cursor.execute(
                    """
                    SELECT id, account_code
                    FROM ledger_accounts
                    WHERE account_code = %s
                    """,
                    (counterparty_account_code,),
                )
                counterparty_account = cursor.fetchone()
                if counterparty_account is None:
                    raise AdminValidationError("Required system account is missing")

                if (
                    direction == DIRECTION_DEBIT
                    and wallet_row["balance_snapshot"] < amount_decimal
                ):
                    raise AdminInsufficientBalanceError("Not enough available balance")

                wallet_balance_after = (
                    wallet_row["balance_snapshot"] + amount_decimal
                    if direction == DIRECTION_CREDIT
                    else wallet_row["balance_snapshot"] - amount_decimal
                ).quantize(Decimal("0.000001"))
                admin_action_id = str(uuid4())
                transaction_id = str(uuid4())
                transaction_type = (
                    ACTION_TYPE_BONUS_GRANT
                    if action_type == ACTION_TYPE_BONUS_GRANT
                    else ACTION_TYPE_ADMIN_ADJUSTMENT
                )
                metadata_json = json.dumps(
                    {
                        "action_type": action_type,
                        "admin_user_id": admin_user_id,
                        "target_user_id": target_user_id,
                        "wallet_type": wallet_type,
                        "direction": direction,
                        "reason": reason,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )

                cursor.execute(
                    """
                    INSERT INTO ledger_transactions (
                        id,
                        user_id,
                        transaction_type,
                        reference_type,
                        reference_id,
                        idempotency_key,
                        metadata_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        transaction_id,
                        target_user_id,
                        transaction_type,
                        "admin_action",
                        admin_action_id,
                        namespaced_idempotency_key,
                        metadata_json,
                    ),
                )

                if direction == DIRECTION_CREDIT:
                    first_entry_account_id = counterparty_account["id"]
                    first_entry_side = "debit"
                    second_entry_account_id = wallet_row["ledger_account_id"]
                    second_entry_side = "credit"
                else:
                    first_entry_account_id = wallet_row["ledger_account_id"]
                    first_entry_side = "debit"
                    second_entry_account_id = counterparty_account["id"]
                    second_entry_side = "credit"

                cursor.execute(
                    """
                    INSERT INTO ledger_entries (
                        id,
                        transaction_id,
                        ledger_account_id,
                        entry_side,
                        amount
                    )
                    VALUES
                        (%s, %s, %s, %s, %s),
                        (%s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        transaction_id,
                        first_entry_account_id,
                        first_entry_side,
                        amount_decimal,
                        str(uuid4()),
                        transaction_id,
                        second_entry_account_id,
                        second_entry_side,
                        amount_decimal,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE wallet_accounts
                    SET balance_snapshot = %s
                    WHERE id = %s
                    """,
                    (wallet_balance_after, wallet_row["id"]),
                )

                cursor.execute(
                    """
                    INSERT INTO admin_actions (
                        id,
                        admin_user_id,
                        target_user_id,
                        action_type,
                        wallet_type,
                        direction,
                        amount,
                        reason,
                        wallet_balance_after,
                        ledger_transaction_id,
                        idempotency_key,
                        request_fingerprint,
                        metadata_json
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                    )
                    """,
                    (
                        admin_action_id,
                        admin_user_id,
                        target_user_id,
                        action_type,
                        wallet_type,
                        direction,
                        amount_decimal,
                        reason,
                        wallet_balance_after,
                        transaction_id,
                        namespaced_idempotency_key,
                        request_fingerprint,
                        metadata_json,
                    ),
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name in {
            "ledger_transactions_idempotency_key_key",
            "admin_actions_idempotency_key_key",
        }:
            existing_action = _get_existing_action_by_idempotency_outside_tx(
                idempotency_key=namespaced_idempotency_key
            )
            if existing_action is not None:
                if existing_action["request_fingerprint"] != request_fingerprint:
                    raise AdminIdempotencyConflictError(
                        "Idempotency key already used with a different payload"
                    ) from exc
                return _response_from_existing(existing_action)
        raise

    return {
        "target_user_id": target_user_id,
        "wallet_type": wallet_type,
        "direction": direction,
        "amount": _format_amount(amount_decimal),
        "wallet_balance_after": _format_amount(wallet_balance_after),
        "ledger_transaction_id": transaction_id,
        "admin_action_id": admin_action_id,
    }


def _ensure_user_exists(*, cursor: psycopg.Cursor, user_id: str, label: str) -> None:
    cursor.execute(
        """
        SELECT 1
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )
    if cursor.fetchone() is None:
        raise AdminNotFoundError(f"{label} not found")


def _get_existing_action_by_idempotency(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            aa.id,
            aa.target_user_id,
            aa.wallet_type,
            aa.direction,
            aa.amount,
            aa.wallet_balance_after,
            aa.ledger_transaction_id,
            aa.request_fingerprint
        FROM admin_actions aa
        WHERE aa.idempotency_key = %s
        """,
        (idempotency_key,),
    )
    return cursor.fetchone()


def _get_existing_action_by_idempotency_outside_tx(
    *,
    idempotency_key: str,
) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            return _get_existing_action_by_idempotency(
                cursor=cursor,
                idempotency_key=idempotency_key,
            )


def _response_from_existing(row: dict[str, object]) -> dict[str, object]:
    return {
        "target_user_id": str(row["target_user_id"]),
        "wallet_type": row["wallet_type"],
        "direction": row["direction"],
        "amount": _format_amount(row["amount"]),
        "wallet_balance_after": _format_amount(row["wallet_balance_after"]),
        "ledger_transaction_id": str(row["ledger_transaction_id"]),
        "admin_action_id": str(row["id"]),
    }


def _parse_wallet_type(value: str) -> str:
    normalized_value = value.strip().lower()
    if normalized_value not in {WALLET_TYPE_CASH, WALLET_TYPE_BONUS}:
        raise AdminValidationError("wallet_type must be cash or bonus")
    return normalized_value


def _parse_direction(value: str) -> str:
    normalized_value = value.strip().lower()
    if normalized_value not in {DIRECTION_CREDIT, DIRECTION_DEBIT}:
        raise AdminValidationError("direction must be credit or debit")
    return normalized_value


def _parse_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise AdminValidationError("amount is not valid") from exc

    if amount <= 0:
        raise AdminValidationError("amount must be greater than zero")

    return amount.quantize(Decimal("0.000001"))


def _parse_reason(value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise AdminValidationError("reason is required")
    if len(normalized_value) > 255:
        raise AdminValidationError("reason is too long")
    return normalized_value


def _build_request_fingerprint(
    *,
    action_type: str,
    target_user_id: str,
    wallet_type: str,
    direction: str,
    amount: Decimal,
    reason: str,
) -> str:
    payload = json.dumps(
        {
            "action_type": action_type,
            "amount": _format_amount(amount),
            "direction": direction,
            "reason": reason,
            "target_user_id": target_user_id,
            "wallet_type": wallet_type,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _build_storage_idempotency_key(
    *,
    scope: str,
    admin_user_id: str,
    target_user_id: str,
    client_idempotency_key: str,
) -> str:
    raw_key = ":".join(
        [scope, admin_user_id, target_user_id, client_idempotency_key.strip()]
    )
    return f"{scope}:{sha256(raw_key.encode('utf-8')).hexdigest()}"


def _format_amount(value: Decimal) -> str:
    return f"{value:.6f}"


def _fetch_financial_transaction_rows(
    *,
    user_id: str | None,
    email_query: str | None,
    wallet_type: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[dict[str, object]]:
    query = """
        WITH round_transaction_links AS (
            SELECT
                pr.id AS round_id,
                pr.user_id,
                pr.game_code,
                pr.wallet_type,
                pr.status AS round_status,
                pr.created_at AS round_created_at,
                pr.closed_at AS round_closed_at,
                pr.access_session_id,
                pr.start_ledger_transaction_id AS ledger_transaction_id
            FROM platform_rounds pr

            UNION ALL

            SELECT
                pr.id AS round_id,
                pr.user_id,
                pr.game_code,
                pr.wallet_type,
                pr.status AS round_status,
                pr.created_at AS round_created_at,
                pr.closed_at AS round_closed_at,
                pr.access_session_id,
                lt.id AS ledger_transaction_id
            FROM platform_rounds pr
            JOIN ledger_transactions lt
              ON lt.reference_type = 'game_session'
             AND lt.reference_id = pr.id
             AND lt.transaction_type = 'win'
        )
        SELECT
            lt.id AS ledger_transaction_id,
            rtl.round_id,
            rtl.user_id,
            u.email AS user_email,
            rtl.game_code,
            rtl.wallet_type,
            rtl.round_status,
            rtl.round_created_at,
            rtl.round_closed_at,
            rtl.access_session_id,
            gas.started_at AS access_session_started_at,
            gas.ended_at AS access_session_ended_at,
            gas.status AS access_session_status,
            lt.transaction_type,
            lt.created_at AS transaction_created_at,
            mgr.grid_size,
            mgr.mine_count,
            mgr.safe_reveals_count,
            COALESCE(
                SUM(CASE WHEN le.entry_side = 'credit' THEN le.amount ELSE 0 END),
                0
            ) AS bank_total_credit,
            COALESCE(
                SUM(CASE WHEN le.entry_side = 'debit' THEN le.amount ELSE 0 END),
                0
            ) AS bank_total_debit
        FROM round_transaction_links rtl
        JOIN ledger_transactions lt ON lt.id = rtl.ledger_transaction_id
        JOIN users u ON u.id = rtl.user_id
        LEFT JOIN game_access_sessions gas ON gas.id = rtl.access_session_id
        LEFT JOIN mines_game_rounds mgr ON mgr.platform_round_id = rtl.round_id
        JOIN ledger_entries le ON le.transaction_id = lt.id
        JOIN ledger_accounts la ON la.id = le.ledger_account_id
        WHERE la.account_code IN (%s, %s, %s, %s)
    """
    params: list[object] = list(FINANCIAL_REPORT_ACCOUNT_CODES)

    if user_id is not None:
        query += "\n          AND rtl.user_id = %s"
        params.append(user_id)
    if email_query is not None:
        query += "\n          AND u.email ILIKE %s"
        params.append(f"%{email_query}%")
    if wallet_type is not None:
        query += "\n          AND rtl.wallet_type = %s"
        params.append(wallet_type)
    if date_from is not None:
        query += "\n          AND lt.created_at >= %s"
        params.append(date_from)
    if date_to is not None:
        query += "\n          AND lt.created_at <= %s"
        params.append(date_to)

    query += """
        GROUP BY
            lt.id,
            rtl.round_id,
            rtl.user_id,
            u.email,
            rtl.game_code,
            rtl.wallet_type,
            rtl.round_status,
            rtl.round_created_at,
            rtl.round_closed_at,
            rtl.access_session_id,
            gas.started_at,
            gas.ended_at,
            gas.status,
            lt.transaction_type,
            lt.created_at,
            mgr.grid_size,
            mgr.mine_count,
            mgr.safe_reveals_count
        ORDER BY lt.created_at DESC, lt.id DESC
    """

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())


def _fetch_financial_transaction_rows_for_session(*, session_id: str) -> list[dict[str, object]]:
    legacy_parts = _parse_legacy_session_id(session_id)
    if legacy_parts is None:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    WITH round_transaction_links AS (
                        SELECT
                            pr.id AS round_id,
                            pr.user_id,
                            pr.game_code,
                            pr.wallet_type,
                            pr.status AS round_status,
                            pr.created_at AS round_created_at,
                            pr.closed_at AS round_closed_at,
                            pr.access_session_id,
                            pr.start_ledger_transaction_id AS ledger_transaction_id
                        FROM platform_rounds pr

                        UNION ALL

                        SELECT
                            pr.id AS round_id,
                            pr.user_id,
                            pr.game_code,
                            pr.wallet_type,
                            pr.status AS round_status,
                            pr.created_at AS round_created_at,
                            pr.closed_at AS round_closed_at,
                            pr.access_session_id,
                            lt.id AS ledger_transaction_id
                        FROM platform_rounds pr
                        JOIN ledger_transactions lt
                          ON lt.reference_type = 'game_session'
                         AND lt.reference_id = pr.id
                         AND lt.transaction_type = 'win'
                    )
                    SELECT
                        lt.id AS ledger_transaction_id,
                        rtl.round_id,
                        rtl.user_id,
                        u.email AS user_email,
                        rtl.game_code,
                        rtl.wallet_type,
                        rtl.round_status,
                        rtl.round_created_at,
                        rtl.round_closed_at,
                        rtl.access_session_id,
                        gas.started_at AS access_session_started_at,
                        gas.ended_at AS access_session_ended_at,
                        gas.status AS access_session_status,
                        lt.transaction_type,
                        lt.created_at AS transaction_created_at,
                        mgr.grid_size,
                        mgr.mine_count,
                        mgr.safe_reveals_count,
                        COALESCE(
                            SUM(CASE WHEN le.entry_side = 'credit' THEN le.amount ELSE 0 END),
                            0
                        ) AS bank_total_credit,
                        COALESCE(
                            SUM(CASE WHEN le.entry_side = 'debit' THEN le.amount ELSE 0 END),
                            0
                        ) AS bank_total_debit
                    FROM round_transaction_links rtl
                    JOIN ledger_transactions lt ON lt.id = rtl.ledger_transaction_id
                    JOIN users u ON u.id = rtl.user_id
                    LEFT JOIN game_access_sessions gas ON gas.id = rtl.access_session_id
                    LEFT JOIN mines_game_rounds mgr ON mgr.platform_round_id = rtl.round_id
                    JOIN ledger_entries le ON le.transaction_id = lt.id
                    JOIN ledger_accounts la ON la.id = le.ledger_account_id
                    WHERE la.account_code IN (%s, %s, %s, %s)
                      AND rtl.access_session_id = %s
                    GROUP BY
                        lt.id,
                        rtl.round_id,
                        rtl.user_id,
                        u.email,
                        rtl.game_code,
                        rtl.wallet_type,
                        rtl.round_status,
                        rtl.round_created_at,
                        rtl.round_closed_at,
                        rtl.access_session_id,
                        gas.started_at,
                        gas.ended_at,
                        gas.status,
                        lt.transaction_type,
                        lt.created_at,
                        mgr.grid_size,
                        mgr.mine_count,
                        mgr.safe_reveals_count
                    ORDER BY lt.created_at ASC, lt.id ASC
                    """,
                    [*FINANCIAL_REPORT_ACCOUNT_CODES, session_id],
                )
                return list(cursor.fetchall())

    legacy_user_id, legacy_date_value = legacy_parts
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH round_transaction_links AS (
                    SELECT
                        pr.id AS round_id,
                        pr.user_id,
                        pr.game_code,
                        pr.wallet_type,
                        pr.status AS round_status,
                        pr.created_at AS round_created_at,
                        pr.closed_at AS round_closed_at,
                        pr.access_session_id,
                        pr.start_ledger_transaction_id AS ledger_transaction_id
                    FROM platform_rounds pr

                    UNION ALL

                    SELECT
                        pr.id AS round_id,
                        pr.user_id,
                        pr.game_code,
                        pr.wallet_type,
                        pr.status AS round_status,
                        pr.created_at AS round_created_at,
                        pr.closed_at AS round_closed_at,
                        pr.access_session_id,
                        lt.id AS ledger_transaction_id
                    FROM platform_rounds pr
                    JOIN ledger_transactions lt
                      ON lt.reference_type = 'game_session'
                     AND lt.reference_id = pr.id
                     AND lt.transaction_type = 'win'
                )
                SELECT
                    lt.id AS ledger_transaction_id,
                    rtl.round_id,
                    rtl.user_id,
                    u.email AS user_email,
                    rtl.game_code,
                    rtl.wallet_type,
                    rtl.round_status,
                    rtl.round_created_at,
                    rtl.round_closed_at,
                    rtl.access_session_id,
                    gas.started_at AS access_session_started_at,
                    gas.ended_at AS access_session_ended_at,
                    gas.status AS access_session_status,
                    lt.transaction_type,
                    lt.created_at AS transaction_created_at,
                    mgr.grid_size,
                    mgr.mine_count,
                    mgr.safe_reveals_count,
                    COALESCE(
                        SUM(CASE WHEN le.entry_side = 'credit' THEN le.amount ELSE 0 END),
                        0
                    ) AS bank_total_credit,
                    COALESCE(
                        SUM(CASE WHEN le.entry_side = 'debit' THEN le.amount ELSE 0 END),
                        0
                    ) AS bank_total_debit
                FROM round_transaction_links rtl
                JOIN ledger_transactions lt ON lt.id = rtl.ledger_transaction_id
                JOIN users u ON u.id = rtl.user_id
                LEFT JOIN game_access_sessions gas ON gas.id = rtl.access_session_id
                LEFT JOIN mines_game_rounds mgr ON mgr.platform_round_id = rtl.round_id
                JOIN ledger_entries le ON le.transaction_id = lt.id
                JOIN ledger_accounts la ON la.id = le.ledger_account_id
                WHERE la.account_code IN (%s, %s, %s, %s)
                  AND rtl.access_session_id IS NULL
                  AND rtl.user_id = %s
                  AND DATE(TIMEZONE('UTC', lt.created_at)) = %s
                GROUP BY
                    lt.id,
                    rtl.round_id,
                    rtl.user_id,
                    u.email,
                    rtl.game_code,
                    rtl.wallet_type,
                    rtl.round_status,
                    rtl.round_created_at,
                    rtl.round_closed_at,
                    rtl.access_session_id,
                    gas.started_at,
                    gas.ended_at,
                    gas.status,
                    lt.transaction_type,
                    lt.created_at,
                    mgr.grid_size,
                    mgr.mine_count,
                    mgr.safe_reveals_count
                ORDER BY lt.created_at ASC, lt.id ASC
                """,
                [*FINANCIAL_REPORT_ACCOUNT_CODES, legacy_user_id, legacy_date_value],
            )
            return list(cursor.fetchall())


def _build_financial_session_identity(row: dict[str, object]) -> tuple[str, bool]:
    access_session_id = row["access_session_id"]
    if access_session_id is not None:
        return str(access_session_id), False
    legacy_session_id = _build_legacy_session_id(
        user_id=str(row["user_id"]),
        transaction_created_at=row["transaction_created_at"],
    )
    return legacy_session_id, True


def _build_legacy_session_id(*, user_id: str, transaction_created_at: datetime) -> str:
    utc_timestamp = transaction_created_at.astimezone(UTC)
    return f"legacy-{user_id}-{utc_timestamp.date().isoformat()}"


def _parse_legacy_session_id(session_id: str) -> tuple[str, date] | None:
    if not session_id.startswith("legacy-"):
        return None
    if len(session_id) <= len("legacy-") + 11:
        raise AdminValidationError("Financial session identifier is not valid")
    legacy_date_raw = session_id[-10:]
    separator = session_id[-11]
    if separator != "-":
        raise AdminValidationError("Financial session identifier is not valid")
    legacy_user_id = session_id[len("legacy-"):-11]
    try:
        return legacy_user_id, date.fromisoformat(legacy_date_raw)
    except ValueError as exc:
        raise AdminValidationError("Financial session identifier is not valid") from exc


def _serialize_session_started_at(row: dict[str, object], *, is_legacy: bool) -> str:
    if is_legacy:
        return row["transaction_created_at"].isoformat()
    started_at = row["access_session_started_at"] or row["transaction_created_at"]
    return started_at.isoformat()


def _serialize_session_ended_at(row: dict[str, object], *, is_legacy: bool) -> str:
    if is_legacy:
        return row["transaction_created_at"].isoformat()
    ended_at = row["access_session_ended_at"] or row["transaction_created_at"]
    return ended_at.isoformat()


def _build_game_enrichment(row: dict[str, object]) -> str:
    if row["grid_size"] is None or row["mine_count"] is None:
        return ""

    status = row["round_status"]
    safe_reveals_count = row["safe_reveals_count"] or 0
    if status == "won":
        return (
            f"Mines: Cashout after {safe_reveals_count} safe reveals "
            f"(grid {row['grid_size']}, mines {row['mine_count']})"
        )
    if status == "lost":
        return (
            f"Mines: Round lost on mine after {safe_reveals_count} safe reveals "
            f"(grid {row['grid_size']}, mines {row['mine_count']})"
        )
    return f"Mines: Grid {row['grid_size']}, mines {row['mine_count']}"


def _parse_report_datetime(
    value: str | None,
    *,
    field_name: str,
    end_of_day: bool,
) -> datetime | None:
    if value is None:
        return None

    normalized_value = value.strip()
    if not normalized_value:
        raise AdminValidationError(f"{field_name} is not valid")

    try:
        if len(normalized_value) == 10:
            parsed_date = date.fromisoformat(normalized_value)
            return datetime.combine(
                parsed_date,
                time.max if end_of_day else time.min,
                tzinfo=UTC,
            )

        parsed_datetime = datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdminValidationError(f"{field_name} is not valid") from exc

    if parsed_datetime.tzinfo is None:
        return parsed_datetime.replace(tzinfo=UTC)
    return parsed_datetime.astimezone(UTC)
