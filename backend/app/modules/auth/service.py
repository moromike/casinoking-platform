from decimal import Decimal
from uuid import uuid4

import psycopg

from app.core.config import settings
from app.db.connection import db_connection
from app.modules.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)

CHIP_CURRENCY = "CHIP"
INITIAL_CASH_CREDIT = Decimal("1000.000000")
HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
PLAYER_CASH_WALLET_TYPE = "cash"
PLAYER_BONUS_WALLET_TYPE = "bonus"
ACCOUNT_STATUS_ACTIVE = "active"
USER_ROLE_ADMIN = "admin"
USER_ROLE_PLAYER = "player"
USER_STATUS_ACTIVE = "active"


class AuthValidationError(Exception):
    pass


class AuthPreconditionError(Exception):
    pass


class AuthConflictError(Exception):
    pass


class AuthInvalidCredentialsError(Exception):
    pass


class AuthForbiddenError(Exception):
    pass


def register_player(
    *,
    email: str,
    password: str,
    site_access_password: str,
) -> dict[str, object]:
    normalized_email = email.strip().lower()
    _validate_register_input(
        email=normalized_email,
        password=password,
        site_access_password=site_access_password,
    )

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                return _create_user_with_bootstrap_credit(
                    cursor=cursor,
                    email=normalized_email,
                    password=password,
                    role=USER_ROLE_PLAYER,
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name == "users_email_key":
            raise AuthConflictError("Email already registered") from exc
        raise

def ensure_local_admin(*, email: str, password: str) -> dict[str, object]:
    normalized_email = email.strip().lower()
    _validate_email_and_password(email=normalized_email, password=password)
    password_hash = hash_password(password)

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE email = %s
                    FOR UPDATE
                    """,
                    (normalized_email,),
                )
                existing_user = cursor.fetchone()

                if existing_user is None:
                    created_user = _create_user_with_bootstrap_credit(
                        cursor=cursor,
                        email=normalized_email,
                        password=password,
                        role=USER_ROLE_ADMIN,
                    )
                    return {
                        "user_id": created_user["user_id"],
                        "email": normalized_email,
                        "role": USER_ROLE_ADMIN,
                        "status": USER_STATUS_ACTIVE,
                        "created": True,
                        "password_reset": False,
                        "bootstrap_transaction_id": created_user[
                            "bootstrap_transaction_id"
                        ],
                    }

                user_id = str(existing_user["id"])
                cursor.execute(
                    """
                    UPDATE users
                    SET role = %s, status = %s
                    WHERE id = %s
                    """,
                    (USER_ROLE_ADMIN, USER_STATUS_ACTIVE, user_id),
                )
                cursor.execute(
                    """
                    INSERT INTO user_credentials (user_id, password_hash)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET password_hash = EXCLUDED.password_hash
                    """,
                    (user_id, password_hash),
                )
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name == "users_email_key":
            raise AuthConflictError("Email already registered") from exc
        raise

    return {
        "user_id": user_id,
        "email": normalized_email,
        "role": USER_ROLE_ADMIN,
        "status": USER_STATUS_ACTIVE,
        "created": False,
        "password_reset": True,
        "bootstrap_transaction_id": None,
    }


def authenticate_user(*, email: str, password: str) -> dict[str, object]:
    normalized_email = email.strip().lower()
    if not normalized_email or not password:
        raise AuthValidationError("Email and password are required")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.role,
                    u.status,
                    uc.password_hash
                FROM users u
                JOIN user_credentials uc ON uc.user_id = u.id
                WHERE u.email = %s
                """,
                (normalized_email,),
            )
            row = cursor.fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        raise AuthInvalidCredentialsError("Invalid email or password")

    if row["status"] != USER_STATUS_ACTIVE:
        raise AuthForbiddenError("Account is not active")

    return {
        "access_token": create_access_token(
            user_id=str(row["id"]),
            role=row["role"],
        ),
        "token_type": "bearer",
    }


def get_user_by_id(user_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, role, status, created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": str(row["id"]),
        "email": row["email"],
        "role": row["role"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
    }


def _validate_register_input(
    *,
    email: str,
    password: str,
    site_access_password: str,
) -> None:
    if site_access_password != settings.site_access_password:
        raise AuthPreconditionError("Invalid site access password")
    _validate_email_and_password(email=email, password=password)


def _validate_email_and_password(*, email: str, password: str) -> None:
    if "@" not in email or "." not in email:
        raise AuthValidationError("Email is not valid")
    if len(password) < 8:
        raise AuthValidationError("Password must be at least 8 characters long")


def _create_user_with_bootstrap_credit(
    *,
    cursor: psycopg.Cursor,
    email: str,
    password: str,
    role: str,
) -> dict[str, object]:
    user_id = str(uuid4())
    player_cash_account_id = str(uuid4())
    player_bonus_account_id = str(uuid4())
    cash_wallet_id = str(uuid4())
    bonus_wallet_id = str(uuid4())
    transaction_id = str(uuid4())
    house_cash_account_id = _get_system_account_id(
        cursor,
        HOUSE_CASH_ACCOUNT_CODE,
    )
    password_hash = hash_password(password)

    cursor.execute(
        """
        INSERT INTO users (id, email, role, status)
        VALUES (%s, %s, %s, %s)
        """,
        (
            user_id,
            email,
            role,
            USER_STATUS_ACTIVE,
        ),
    )
    cursor.execute(
        """
        INSERT INTO user_credentials (user_id, password_hash)
        VALUES (%s, %s)
        """,
        (
            user_id,
            password_hash,
        ),
    )
    cursor.execute(
        """
        INSERT INTO ledger_accounts (
            id,
            account_code,
            account_type,
            owner_user_id,
            currency_code,
            status
        )
        VALUES
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s)
        """,
        (
            player_cash_account_id,
            f"PLAYER_CASH_{user_id}",
            "player_cash",
            user_id,
            CHIP_CURRENCY,
            ACCOUNT_STATUS_ACTIVE,
            player_bonus_account_id,
            f"PLAYER_BONUS_{user_id}",
            "player_bonus",
            user_id,
            CHIP_CURRENCY,
            ACCOUNT_STATUS_ACTIVE,
        ),
    )
    cursor.execute(
        """
        INSERT INTO wallet_accounts (
            id,
            user_id,
            ledger_account_id,
            wallet_type,
            currency_code,
            balance_snapshot,
            status
        )
        VALUES
            (%s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            cash_wallet_id,
            user_id,
            player_cash_account_id,
            PLAYER_CASH_WALLET_TYPE,
            CHIP_CURRENCY,
            Decimal("0.000000"),
            ACCOUNT_STATUS_ACTIVE,
            bonus_wallet_id,
            user_id,
            player_bonus_account_id,
            PLAYER_BONUS_WALLET_TYPE,
            CHIP_CURRENCY,
            Decimal("0.000000"),
            ACCOUNT_STATUS_ACTIVE,
        ),
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
            user_id,
            "signup_credit",
            "user",
            user_id,
            f"signup-{user_id}",
            "{}",
        ),
    )
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
            player_cash_account_id,
            "credit",
            INITIAL_CASH_CREDIT,
            str(uuid4()),
            transaction_id,
            house_cash_account_id,
            "debit",
            INITIAL_CASH_CREDIT,
        ),
    )
    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot + %s
        WHERE id = %s
        """,
        (
            INITIAL_CASH_CREDIT,
            cash_wallet_id,
        ),
    )

    return {
        "user_id": user_id,
        "wallets": [
            {
                "wallet_type": PLAYER_CASH_WALLET_TYPE,
                "currency_code": CHIP_CURRENCY,
                "balance_snapshot": f"{INITIAL_CASH_CREDIT:.6f}",
            },
            {
                "wallet_type": PLAYER_BONUS_WALLET_TYPE,
                "currency_code": CHIP_CURRENCY,
                "balance_snapshot": "0.000000",
            },
        ],
        "bootstrap_transaction_id": transaction_id,
    }


def _get_system_account_id(cursor: psycopg.Cursor, account_code: str) -> str:
    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (account_code,),
    )
    row = cursor.fetchone()
    if row is None:
        raise AuthPreconditionError(
            f"Required system account '{account_code}' is missing"
        )
    return str(row["id"])
