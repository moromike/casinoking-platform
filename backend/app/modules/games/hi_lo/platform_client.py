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

GAME_CODE = "hi_lo"
HI_LO_LEDGER_GRID_SIZE = 52
HI_LO_LEDGER_RISK_INDEX = 1


class HiLoPlatformValidationError(RuntimeError):
    pass


class HiLoPlatformInsufficientBalanceError(RuntimeError):
    pass


class HiLoPlatformIdempotencyConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class HiLoPlatformRoundOpenResult:
    platform_round_id: str
    wallet_account_id: str
    wallet_balance_after_start: Decimal
    ledger_transaction_id: str
    table_session_id: str
    table_session: dict[str, object]


@dataclass(frozen=True)
class HiLoPlatformRoundSettlementResult:
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
    bet_amount: Decimal,
    wallet_type: str,
    title_code: str,
    site_code: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
    request_fingerprint: str | None = None,
) -> HiLoPlatformRoundOpenResult:
    try:
        result = open_game_round(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            idempotency_key=idempotency_key,
            grid_size=HI_LO_LEDGER_GRID_SIZE,
            mine_count=HI_LO_LEDGER_RISK_INDEX,
            bet_amount=bet_amount,
            wallet_type=wallet_type,
            table_session_id=table_session_id,
            access_session_id=access_session_id,
            title_code=title_code,
            site_code=site_code,
            request_fingerprint=request_fingerprint,
            game_config_payload={
                "deck": "standard_52",
            },
        )
    except PlatformRoundInsufficientBalanceError as exc:
        raise HiLoPlatformInsufficientBalanceError(str(exc)) from exc
    except PlatformRoundValidationError as exc:
        raise HiLoPlatformValidationError(str(exc)) from exc
    except TableSessionLimitExceededError as exc:
        raise HiLoPlatformValidationError(str(exc)) from exc
    except (
        TableSessionNotFoundError,
        TableSessionStateConflictError,
        TableSessionValidationError,
    ) as exc:
        raise HiLoPlatformValidationError(str(exc)) from exc

    return HiLoPlatformRoundOpenResult(
        platform_round_id=str(result["platform_round_id"]),
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
    successful_predictions_count: int,
    idempotency_key: str,
) -> HiLoPlatformRoundSettlementResult:
    try:
        result = settle_game_round_win(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            payout_amount=payout_amount,
            safe_reveals_count=successful_predictions_count,
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
                raise HiLoPlatformValidationError("Cashout snapshot is not available")
            wallet_balance_after = snapshot["wallet_balance_after"]
        return HiLoPlatformRoundSettlementResult(
            platform_round_id=str(result.get("platform_round_id", round_id)),
            wallet_balance_after=Decimal(wallet_balance_after),
            ledger_transaction_id=str(result["ledger_transaction_id"]),
            already_exists=bool(result["already_exists"]),
        )
    except PlatformRoundIdempotencyConflictError as exc:
        raise HiLoPlatformIdempotencyConflictError(str(exc)) from exc
    except PlatformRoundValidationError as exc:
        raise HiLoPlatformValidationError(str(exc)) from exc


def settle_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    successful_predictions_count: int,
) -> HiLoPlatformRoundSettlementResult:
    try:
        result = settle_game_round_loss(
            cursor=cursor,
            game_code=GAME_CODE,
            user_id=user_id,
            game_session_id=round_id,
            safe_reveals_count=successful_predictions_count,
            record_settlement_ledger_transaction=True,
        )
        return HiLoPlatformRoundSettlementResult(
            platform_round_id=str(result.get("platform_round_id", round_id)),
            wallet_balance_after=Decimal(result["wallet_balance_after"]),
            ledger_transaction_id=str(result["bet_transaction_id"]),
        )
    except PlatformRoundValidationError as exc:
        raise HiLoPlatformValidationError(str(exc)) from exc
