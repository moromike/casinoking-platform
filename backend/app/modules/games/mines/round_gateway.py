from dataclasses import dataclass
from decimal import Decimal

import psycopg

from app.modules.games.mines.exceptions import (
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesValidationError,
)
from app.modules.platform.rounds.service import (
    PlatformRoundIdempotencyConflictError,
    PlatformRoundInsufficientBalanceError,
    PlatformRoundValidationError,
    get_existing_round_win_by_key,
    get_mines_round_cashout_snapshot,
    is_mines_round_open_idempotency_violation,
    is_mines_round_settlement_idempotency_violation,
    namespace_mines_round_win_idempotency_key,
    open_mines_round,
    settle_mines_round_loss,
    settle_mines_round_win,
)
from app.modules.platform.table_sessions.service import (
    TableSessionLimitExceededError,
    TableSessionNotFoundError,
    TableSessionStateConflictError,
    TableSessionValidationError,
)


@dataclass(frozen=True)
class MinesPlatformRoundOpenResult:
    """Platform-owned facts produced while opening a Mines round."""

    platform_round_id: str
    wallet_account_id: str
    wallet_balance_after_start: Decimal
    ledger_transaction_id: str
    table_session_id: str
    table_session: dict[str, object]


@dataclass(frozen=True)
class MinesPlatformRoundWinResult:
    """Platform-owned facts produced while settling a Mines round as won."""

    platform_round_id: str
    wallet_balance_after: Decimal
    ledger_transaction_id: str
    already_exists: bool


@dataclass(frozen=True)
class MinesPlatformRoundLossResult:
    """Platform-owned facts produced while settling a Mines round as lost."""

    platform_round_id: str
    wallet_balance_after: Decimal
    bet_transaction_id: str
    safe_reveals_count: int


def open_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> MinesPlatformRoundOpenResult:
    """Open the platform-owned economic round for a Mines game round.

    M1 keeps platform_round_id equal to the current game_round_id for schema
    compatibility, but the result names it explicitly so the game service does
    not treat the platform round as an implicit session detail.

    Returns wallet_account_id, wallet_balance_after_start, ledger_transaction_id,
    and platform_round_id.

    Translates platform exceptions into Mines-domain exceptions.
    """
    try:
        result = open_mines_round(
            cursor=cursor,
            user_id=user_id,
            game_session_id=game_round_id,
            idempotency_key=idempotency_key,
            grid_size=grid_size,
            mine_count=mine_count,
            bet_amount=bet_amount,
            wallet_type=wallet_type,
            table_session_id=table_session_id,
            access_session_id=access_session_id,
        )
        return MinesPlatformRoundOpenResult(
            platform_round_id=game_round_id,
            wallet_account_id=str(result["wallet_account_id"]),
            wallet_balance_after_start=Decimal(result["wallet_balance_after_start"]),
            ledger_transaction_id=str(result["ledger_transaction_id"]),
            table_session_id=str(result["table_session_id"]),
            table_session=dict(result["table_session"]),
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
    except PlatformRoundInsufficientBalanceError as exc:
        raise MinesInsufficientBalanceError(str(exc)) from exc
    except TableSessionLimitExceededError as exc:
        raise MinesValidationError(str(exc)) from exc
    except (
        TableSessionNotFoundError,
        TableSessionStateConflictError,
        TableSessionValidationError,
    ) as exc:
        raise MinesValidationError(str(exc)) from exc


def get_existing_cashout_by_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    return get_existing_round_win_by_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )


def get_cashout_snapshot(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
) -> dict[str, object] | None:
    return get_mines_round_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_round_id,
    )


def build_cashout_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return namespace_mines_round_win_idempotency_key(
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def is_open_round_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return is_mines_round_open_idempotency_violation(exc)


def is_settlement_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return is_mines_round_settlement_idempotency_violation(exc)


def get_round_start_snapshot(
    *,
    cursor: psycopg.Cursor,
    platform_round_id: str,
) -> dict[str, object]:
    """Read wallet_balance_after_start and start_ledger_transaction_id from platform_rounds.

    Used by the game service for idempotent response building without
    directly accessing platform field names in business logic.
    """
    cursor.execute(
        """
        SELECT
            pr.wallet_balance_after_start,
            pr.start_ledger_transaction_id
        FROM platform_rounds pr
        WHERE pr.id = %s
        """,
        (platform_round_id,),
    )
    row = cursor.fetchone()
    if row is None:
        raise MinesValidationError(f"Platform round {platform_round_id} not found")
    return {
        "wallet_balance_after_start": row["wallet_balance_after_start"],
        "ledger_transaction_id": str(row["start_ledger_transaction_id"]),
    }


def settle_round_win(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
) -> MinesPlatformRoundWinResult:
    try:
        result = settle_mines_round_win(
            cursor=cursor,
            user_id=user_id,
            game_session_id=game_round_id,
            payout_amount=payout_amount,
            safe_reveals_count=safe_reveals_count,
            idempotency_key=idempotency_key,
        )
        wallet_balance_after = result.get("wallet_balance_after")
        if wallet_balance_after is None:
            snapshot = get_mines_round_cashout_snapshot(
                cursor=cursor,
                user_id=user_id,
                game_session_id=game_round_id,
            )
            if snapshot is None:
                raise MinesValidationError("Cashout snapshot is not available")
            wallet_balance_after = snapshot["wallet_balance_after"]
        return MinesPlatformRoundWinResult(
            platform_round_id=game_round_id,
            wallet_balance_after=Decimal(wallet_balance_after),
            ledger_transaction_id=str(result["ledger_transaction_id"]),
            already_exists=bool(result["already_exists"]),
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
    except PlatformRoundIdempotencyConflictError as exc:
        raise MinesIdempotencyConflictError(str(exc)) from exc


def settle_round_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    safe_reveals_count: int,
) -> MinesPlatformRoundLossResult:
    try:
        result = settle_mines_round_loss(
            cursor=cursor,
            user_id=user_id,
            game_session_id=game_round_id,
            safe_reveals_count=safe_reveals_count,
        )
        return MinesPlatformRoundLossResult(
            platform_round_id=game_round_id,
            wallet_balance_after=Decimal(result["wallet_balance_after"]),
            bet_transaction_id=str(result["bet_transaction_id"]),
            safe_reveals_count=int(result["safe_reveals_count"]),
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
