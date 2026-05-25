from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import psycopg

from app.modules.platform.rounds.service import (
    PlatformRoundIdempotencyConflictError,
    PlatformRoundInsufficientBalanceError,
    PlatformRoundValidationError,
    get_game_round_cashout_snapshot,
    namespace_game_round_win_idempotency_key,
    open_game_round,
    settle_game_round_loss,
    settle_game_round_win,
)
from app.modules.platform.table_sessions.service import (
    TableSessionLimitExceededError,
    TableSessionNotFoundError,
    TableSessionStateConflictError,
    TableSessionValidationError,
)

GAME_CODE = "boxe"
DIFFICULTY_RISK_INDEX = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}


class BoxePlatformValidationError(RuntimeError):
    pass


class BoxePlatformInsufficientBalanceError(RuntimeError):
    pass


class BoxePlatformIdempotencyConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class BoxePlatformRoundOpenResult:
    platform_round_id: str
    wallet_account_id: str
    wallet_balance_after_start: Decimal
    ledger_transaction_id: str
    table_session_id: str
    table_session: dict[str, object]


@dataclass(frozen=True)
class BoxePlatformRoundSettlementResult:
    platform_round_id: str
    wallet_balance_after: Decimal
    ledger_transaction_id: str
    already_exists: bool = False


def open_round(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    idempotency_key: str,
    rows: int,
    difficulty: str,
    bet_amount: Decimal,
    wallet_type: str,
    title_code: str,
    site_code: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> BoxePlatformRoundOpenResult:
    try:
        result = open_game_round(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            idempotency_key=idempotency_key,
            grid_size=rows,
            mine_count=DIFFICULTY_RISK_INDEX[difficulty],
            bet_amount=bet_amount,
            wallet_type=wallet_type,
            table_session_id=table_session_id,
            access_session_id=access_session_id,
            title_code=title_code,
            site_code=site_code,
            game_config_payload={
                "rows": rows,
                "difficulty": difficulty,
            },
        )
    except PlatformRoundInsufficientBalanceError as exc:
        raise BoxePlatformInsufficientBalanceError(str(exc)) from exc
    except PlatformRoundValidationError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc
    except TableSessionLimitExceededError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc
    except (
        TableSessionNotFoundError,
        TableSessionStateConflictError,
        TableSessionValidationError,
    ) as exc:
        raise BoxePlatformValidationError(str(exc)) from exc

    return BoxePlatformRoundOpenResult(
        platform_round_id=round_id,
        wallet_account_id=str(result["wallet_account_id"]),
        wallet_balance_after_start=Decimal(result["wallet_balance_after_start"]),
        ledger_transaction_id=str(result["ledger_transaction_id"]),
        table_session_id=str(result["table_session_id"]),
        table_session=dict(result["table_session"]),
    )


def build_cashout_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return namespace_game_round_win_idempotency_key(
        game_code=GAME_CODE,
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def settle_win(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    payout_amount: Decimal,
    safe_picks_count: int,
    idempotency_key: str,
) -> BoxePlatformRoundSettlementResult:
    try:
        result = settle_game_round_win(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            payout_amount=payout_amount,
            safe_reveals_count=safe_picks_count,
            idempotency_key=idempotency_key,
        )
        wallet_balance_after = result.get("wallet_balance_after")
        if wallet_balance_after is None:
            snapshot = get_game_round_cashout_snapshot(
                cursor=cursor,
                user_id=user_id,
                game_session_id=round_id,
            )
            if snapshot is None:
                raise BoxePlatformValidationError("Cashout snapshot is not available")
            wallet_balance_after = snapshot["wallet_balance_after"]
        return BoxePlatformRoundSettlementResult(
            platform_round_id=round_id,
            wallet_balance_after=Decimal(wallet_balance_after),
            ledger_transaction_id=str(result["ledger_transaction_id"]),
            already_exists=bool(result["already_exists"]),
        )
    except PlatformRoundIdempotencyConflictError as exc:
        raise BoxePlatformIdempotencyConflictError(str(exc)) from exc
    except PlatformRoundValidationError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc


def settle_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    safe_picks_count: int,
) -> BoxePlatformRoundSettlementResult:
    try:
        result = settle_game_round_loss(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            safe_reveals_count=safe_picks_count,
        )
        return BoxePlatformRoundSettlementResult(
            platform_round_id=round_id,
            wallet_balance_after=Decimal(result["wallet_balance_after"]),
            ledger_transaction_id=str(result["bet_transaction_id"]),
        )
    except PlatformRoundValidationError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc
