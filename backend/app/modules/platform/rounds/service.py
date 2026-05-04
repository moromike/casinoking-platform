from decimal import Decimal
import json
from uuid import uuid4

import psycopg

from app.modules.platform.table_sessions.service import (
    GAME_CODE_MINES,
    TableSessionLimitExceededError,
    TableSessionNotFoundError,
    TableSessionStateConflictError,
    TableSessionValidationError,
    consume_reserved_loss,
    release_reserved_loss,
    validate_and_reserve_round_exposure,
)

HOUSE_CASH_ACCOUNT_CODE = "HOUSE_CASH"
TITLE_CODE_MINES_CLASSIC = "mines_classic"
SITE_CODE_CASINOKING = "casinoking"
MINES_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS = frozenset(
    {
        "ledger_transactions_idempotency_key_key",
        "platform_rounds_user_idempotency_key_key",
    }
)
MINES_ROUND_SETTLEMENT_IDEMPOTENCY_CONSTRAINT = "ledger_transactions_idempotency_key_key"


class PlatformRoundValidationError(Exception):
    pass


class PlatformRoundInsufficientBalanceError(Exception):
    pass


class PlatformRoundIdempotencyConflictError(Exception):
    pass


def namespace_mines_round_win_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return f"mines:cashout:{user_id}:{idempotency_key}"


def is_mines_round_open_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return exc.diag.constraint_name in MINES_ROUND_OPEN_IDEMPOTENCY_CONSTRAINTS


def is_mines_round_settlement_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return exc.diag.constraint_name == MINES_ROUND_SETTLEMENT_IDEMPOTENCY_CONSTRAINT


def open_mines_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
    title_code: str | None = None,
    site_code: str | None = None,
) -> dict[str, object]:
    normalized_title_code = title_code or TITLE_CODE_MINES_CLASSIC
    normalized_site_code = site_code or SITE_CODE_CASINOKING
    table_session = validate_and_reserve_round_exposure(
        cursor=cursor,
        user_id=user_id,
        table_session_id=table_session_id,
        game_code=GAME_CODE_MINES,
        wallet_type=wallet_type,
        bet_amount=bet_amount,
        access_session_id=access_session_id,
        title_code=normalized_title_code,
        site_code=normalized_site_code,
    )
    cursor.execute(
        """
        SELECT
            wa.id,
            wa.wallet_type,
            wa.balance_snapshot,
            la.id AS ledger_account_id
        FROM wallet_accounts wa
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE wa.user_id = %s
          AND wa.wallet_type = %s
          AND wa.status = 'active'
        FOR UPDATE
        """,
        (user_id, wallet_type),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundValidationError("Selected wallet is not available")
    if wallet_row["balance_snapshot"] < bet_amount:
        raise PlatformRoundInsufficientBalanceError("Not enough available balance")

    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (HOUSE_CASH_ACCOUNT_CODE,),
    )
    house_cash_account = cursor.fetchone()
    if house_cash_account is None:
        raise PlatformRoundValidationError("Required system account is missing")

    transaction_id = str(uuid4())
    wallet_balance_after_start = wallet_row["balance_snapshot"] - bet_amount
    namespaced_idempotency_key = f"mines:start:{user_id}:{idempotency_key}"

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
            "bet",
            "game_session",
            game_session_id,
            namespaced_idempotency_key,
            json.dumps(
                {
                    "game_code": GAME_CODE_MINES,
                    "title_code": normalized_title_code,
                    "site_code": normalized_site_code,
                    "wallet_type": wallet_type,
                    "grid_size": grid_size,
                    "mine_count": mine_count,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
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
            wallet_row["ledger_account_id"],
            "debit",
            bet_amount,
            str(uuid4()),
            transaction_id,
            house_cash_account["id"],
            "credit",
            bet_amount,
        ),
    )
    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot - %s
        WHERE id = %s
        """,
        (bet_amount, wallet_row["id"]),
    )

    return {
        "wallet_account_id": wallet_row["id"],
        "wallet_balance_after_start": wallet_balance_after_start,
        "ledger_transaction_id": transaction_id,
        "table_session_id": table_session["id"],
        "table_session": table_session,
    }


def get_existing_round_win_by_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT id, reference_id
        FROM ledger_transactions
        WHERE idempotency_key = %s
          AND transaction_type = 'win'
          AND reference_type = 'game_session'
        """,
        (idempotency_key,),
    )
    return cursor.fetchone()


def get_mines_round_cashout_snapshot(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            pr.payout_amount AS payout_current,
            (pr.wallet_balance_after_start + pr.payout_amount) AS wallet_balance_after
        FROM platform_rounds pr
        WHERE pr.id = %s
          AND pr.user_id = %s
        """,
        (game_session_id, user_id),
    )
    return cursor.fetchone()


def settle_mines_round_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
    safe_reveals_count: int,
) -> dict[str, object]:
    cursor.execute(
        """
        SELECT
            wa.id,
            wa.balance_snapshot,
            pr.table_session_id,
            pr.bet_amount
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
        FOR UPDATE OF wa
        """,
        (game_session_id, user_id),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundValidationError("Selected wallet is not available")

    cursor.execute(
        """
        SELECT id
        FROM ledger_transactions
        WHERE user_id = %s
          AND transaction_type = 'bet'
          AND reference_type = 'game_session'
          AND reference_id = %s
        """,
        (user_id, game_session_id),
    )
    bet_row = cursor.fetchone()
    if bet_row is None:
        raise PlatformRoundValidationError("Round bet transaction is not available")

    cursor.execute(
        """
        SELECT id
        FROM ledger_transactions
        WHERE user_id = %s
          AND transaction_type = 'win'
          AND reference_type = 'game_session'
          AND reference_id = %s
        """,
        (user_id, game_session_id),
    )
    win_row = cursor.fetchone()
    if win_row is not None:
        raise PlatformRoundValidationError("Round is already settled as win")

    table_session = consume_reserved_loss(
        cursor=cursor,
        table_session_id=(
            str(wallet_row["table_session_id"]) if wallet_row["table_session_id"] else None
        ),
        bet_amount=Decimal(wallet_row["bet_amount"]),
    )

    return {
        "bet_transaction_id": str(bet_row["id"]),
        "wallet_balance_after": wallet_row["balance_snapshot"],
        "safe_reveals_count": safe_reveals_count,
        "table_session": table_session,
    }


def settle_mines_round_win(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_session_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
) -> dict[str, object]:
    existing_cashout = get_existing_round_win_by_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )
    if existing_cashout is not None:
        if str(existing_cashout["reference_id"]) != game_session_id:
            raise PlatformRoundIdempotencyConflictError(
                "Idempotency key already used with a different payload"
            )
        return {
            "ledger_transaction_id": str(existing_cashout["id"]),
            "already_exists": True,
        }

    cursor.execute(
        """
        SELECT
            wa.id,
            wa.balance_snapshot,
            la.id AS ledger_account_id,
            pr.table_session_id,
            pr.bet_amount
        FROM platform_rounds pr
        JOIN wallet_accounts wa ON wa.id = pr.wallet_account_id
        JOIN ledger_accounts la ON la.id = wa.ledger_account_id
        WHERE pr.id = %s
          AND pr.user_id = %s
        FOR UPDATE OF wa
        """,
        (game_session_id, user_id),
    )
    wallet_row = cursor.fetchone()
    if wallet_row is None:
        raise PlatformRoundValidationError("Selected wallet is not available")

    cursor.execute(
        """
        SELECT id
        FROM ledger_accounts
        WHERE account_code = %s
        """,
        (HOUSE_CASH_ACCOUNT_CODE,),
    )
    house_cash_account = cursor.fetchone()
    if house_cash_account is None:
        raise PlatformRoundValidationError("Required system account is missing")

    wallet_balance_after = (
        wallet_row["balance_snapshot"] + payout_amount
    ).quantize(Decimal("0.000001"))
    transaction_id = str(uuid4())

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
            "win",
            "game_session",
            game_session_id,
            idempotency_key,
            json.dumps(
                {
                    "game_code": GAME_CODE_MINES,
                    "safe_reveals_count": safe_reveals_count,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
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
            house_cash_account["id"],
            "debit",
            payout_amount,
            str(uuid4()),
            transaction_id,
            wallet_row["ledger_account_id"],
            "credit",
            payout_amount,
        ),
    )
    cursor.execute(
        """
        UPDATE wallet_accounts
        SET balance_snapshot = balance_snapshot + %s
        WHERE id = %s
        """,
        (payout_amount, wallet_row["id"]),
    )
    table_session = release_reserved_loss(
        cursor=cursor,
        table_session_id=(
            str(wallet_row["table_session_id"]) if wallet_row["table_session_id"] else None
        ),
        bet_amount=Decimal(wallet_row["bet_amount"]),
        payout_amount=payout_amount,
    )

    return {
        "ledger_transaction_id": transaction_id,
        "wallet_balance_after": wallet_balance_after,
        "already_exists": False,
        "table_session": table_session,
    }
