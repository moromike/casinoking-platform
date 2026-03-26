from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from uuid import uuid4

import psycopg

from app.db.connection import db_connection

ACTION_TYPE_ADMIN_ADJUSTMENT = "admin_adjustment"
ACTION_TYPE_BONUS_GRANT = "bonus_grant"
CHIP_CURRENCY = "CHIP"
DIRECTION_CREDIT = "credit"
DIRECTION_DEBIT = "debit"
HOUSE_BONUS_ACCOUNT_CODE = "HOUSE_BONUS"
HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
PROMO_RESERVE_ACCOUNT_CODE = "PROMO_RESERVE"
WALLET_TYPE_BONUS = "bonus"
WALLET_TYPE_CASH = "cash"


class AdminValidationError(Exception):
    pass


class AdminNotFoundError(Exception):
    pass


class AdminIdempotencyConflictError(Exception):
    pass


class AdminInsufficientBalanceError(Exception):
    pass


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
                    SELECT id, email, role, status, created_at
                    FROM users
                    WHERE email ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT 100
                    """,
                    (f"%{normalized_query}%",),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, email, role, status, created_at
                    FROM users
                    ORDER BY created_at DESC
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
        }
        for row in rows
    ]


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
