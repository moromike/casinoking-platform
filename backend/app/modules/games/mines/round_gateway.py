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


def open_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    bet_amount: Decimal,
    wallet_type: str,
) -> dict[str, object]:
    try:
        return open_mines_round(
            cursor=cursor,
            user_id=user_id,
            game_session_id=session_id,
            idempotency_key=idempotency_key,
            grid_size=grid_size,
            mine_count=mine_count,
            bet_amount=bet_amount,
            wallet_type=wallet_type,
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
    except PlatformRoundInsufficientBalanceError as exc:
        raise MinesInsufficientBalanceError(str(exc)) from exc


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
    session_id: str,
) -> dict[str, object] | None:
    return get_mines_round_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_session_id=session_id,
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


def settle_round_win(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
) -> dict[str, object]:
    try:
        return settle_mines_round_win(
            cursor=cursor,
            user_id=user_id,
            game_session_id=session_id,
            payout_amount=payout_amount,
            safe_reveals_count=safe_reveals_count,
            idempotency_key=idempotency_key,
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
    except PlatformRoundIdempotencyConflictError as exc:
        raise MinesIdempotencyConflictError(str(exc)) from exc


def settle_round_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    session_id: str,
    safe_reveals_count: int,
) -> dict[str, object]:
    try:
        return settle_mines_round_loss(
            cursor=cursor,
            user_id=user_id,
            game_session_id=session_id,
            safe_reveals_count=safe_reveals_count,
        )
    except PlatformRoundValidationError as exc:
        raise MinesValidationError(str(exc)) from exc
