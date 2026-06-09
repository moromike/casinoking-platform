from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import psycopg

from app.modules.platform.game_modules.adapter import (
    PlatformGameAdapter,
    PlatformOpenRoundRequest,
    PlatformOpenRoundResult,
    PlatformSettlementResult,
    PlatformSettleLossRequest,
    PlatformSettleWinRequest,
)
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


class InProcessHiLoPlatformAdapter:
    """HI-LO adapter over the current in-process platform services."""

    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult:
        _ensure_hi_lo_game_code(request.game_code)
        try:
            result = open_game_round(
                cursor=request.cursor,
                game_code=GAME_CODE,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
                idempotency_key=request.idempotency_key,
                grid_size=HI_LO_LEDGER_GRID_SIZE,
                mine_count=HI_LO_LEDGER_RISK_INDEX,
                bet_amount=request.bet_amount,
                wallet_type=request.wallet_source,
                table_session_id=request.table_session_ref,
                access_session_id=request.access_session_ref,
                title_code=request.title_code,
                site_code=request.site_code,
                request_fingerprint=request.request_fingerprint,
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

        return PlatformOpenRoundResult(
            platform_round_ref=str(result["platform_round_id"]),
            wallet_account_ref=str(result["wallet_account_id"]),
            wallet_balance_after_start=Decimal(result["wallet_balance_after_start"]),
            ledger_transaction_ref=str(result["ledger_transaction_id"]),
            table_session_ref=str(result["table_session_id"]),
            table_session=dict(result["table_session"]),
        )

    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult:
        _ensure_hi_lo_game_code(request.game_code)
        try:
            result = settle_game_round_win(
                cursor=request.cursor,
                game_code=GAME_CODE,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
                payout_amount=request.payout_amount,
                safe_reveals_count=request.successful_steps,
                idempotency_key=request.idempotency_key,
            )
        except PlatformRoundIdempotencyConflictError as exc:
            raise HiLoPlatformIdempotencyConflictError(str(exc)) from exc
        except PlatformRoundValidationError as exc:
            raise HiLoPlatformValidationError(str(exc)) from exc

        wallet_balance_after = result.get("wallet_balance_after")
        if wallet_balance_after is None:
            snapshot = get_game_round_cashout_snapshot(
                cursor=request.cursor,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
            )
            if snapshot is None:
                raise HiLoPlatformValidationError("Cashout snapshot is not available")
            wallet_balance_after = snapshot["wallet_balance_after"]

        return PlatformSettlementResult(
            platform_round_ref=str(result.get("platform_round_id", request.game_round_ref)),
            wallet_balance_after=Decimal(wallet_balance_after),
            ledger_transaction_ref=str(result["ledger_transaction_id"]),
            already_exists=bool(result["already_exists"]),
        )

    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult:
        _ensure_hi_lo_game_code(request.game_code)
        try:
            result = settle_game_round_loss(
                cursor=request.cursor,
                game_code=GAME_CODE,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
                safe_reveals_count=request.successful_steps,
                record_settlement_ledger_transaction=True,
            )
        except PlatformRoundValidationError as exc:
            raise HiLoPlatformValidationError(str(exc)) from exc

        return PlatformSettlementResult(
            platform_round_ref=str(result.get("platform_round_id", request.game_round_ref)),
            wallet_balance_after=Decimal(result["wallet_balance_after"]),
            ledger_transaction_ref=str(result["bet_transaction_id"]),
        )


_DEFAULT_PLATFORM_ADAPTER: PlatformGameAdapter = InProcessHiLoPlatformAdapter()


def get_default_platform_adapter() -> PlatformGameAdapter:
    return _DEFAULT_PLATFORM_ADAPTER


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
    result = get_default_platform_adapter().open_round(
        PlatformOpenRoundRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=round_id,
            idempotency_key=idempotency_key,
            title_code=title_code,
            site_code=site_code,
            wallet_source=wallet_type,
            bet_amount=bet_amount,
            table_session_ref=table_session_id,
            access_session_ref=access_session_id,
            request_fingerprint=request_fingerprint,
            game_config={
                "deck": "standard_52",
            },
        )
    )
    return HiLoPlatformRoundOpenResult(
        platform_round_id=result.platform_round_ref,
        wallet_account_id=result.wallet_account_ref,
        wallet_balance_after_start=result.wallet_balance_after_start,
        ledger_transaction_id=result.ledger_transaction_ref,
        table_session_id=result.table_session_ref,
        table_session=result.table_session,
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
    result = get_default_platform_adapter().settle_win(
        PlatformSettleWinRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=round_id,
            payout_amount=payout_amount,
            successful_steps=successful_predictions_count,
            idempotency_key=idempotency_key,
        )
    )
    return HiLoPlatformRoundSettlementResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        ledger_transaction_id=result.ledger_transaction_ref,
        already_exists=result.already_exists,
    )


def settle_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    successful_predictions_count: int,
) -> HiLoPlatformRoundSettlementResult:
    result = get_default_platform_adapter().settle_loss(
        PlatformSettleLossRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=round_id,
            successful_steps=successful_predictions_count,
        )
    )
    return HiLoPlatformRoundSettlementResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        ledger_transaction_id=result.ledger_transaction_ref,
    )


def _ensure_hi_lo_game_code(game_code: str) -> None:
    if game_code != GAME_CODE:
        raise HiLoPlatformValidationError("HI-LO platform adapter received the wrong game code")
