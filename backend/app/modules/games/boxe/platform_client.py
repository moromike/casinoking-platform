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
    table_session: dict[str, object] | None = None


class InProcessBoxePlatformAdapter:
    """BOXE adapter over the current in-process platform services."""

    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult:
        _ensure_boxe_game_code(request.game_code)
        rows = int(request.game_config["rows"])
        difficulty = str(request.game_config["difficulty"])
        result = _open_round_in_process(
            cursor=request.cursor,
            user_id=request.player_ref,
            round_id=request.game_round_ref,
            idempotency_key=request.idempotency_key,
            rows=rows,
            difficulty=difficulty,
            bet_amount=request.bet_amount,
            wallet_type=request.wallet_source,
            title_code=request.title_code,
            site_code=request.site_code,
            table_session_id=request.table_session_ref,
            access_session_id=request.access_session_ref,
        )
        return PlatformOpenRoundResult(
            platform_round_ref=result.platform_round_id,
            wallet_account_ref=result.wallet_account_id,
            wallet_balance_after_start=result.wallet_balance_after_start,
            ledger_transaction_ref=result.ledger_transaction_id,
            table_session_ref=result.table_session_id,
            table_session=result.table_session,
        )

    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult:
        _ensure_boxe_game_code(request.game_code)
        result = _settle_win_in_process(
            cursor=request.cursor,
            user_id=request.player_ref,
            round_id=request.game_round_ref,
            payout_amount=request.payout_amount,
            safe_picks_count=request.successful_steps,
            idempotency_key=request.idempotency_key,
        )
        return PlatformSettlementResult(
            platform_round_ref=result.platform_round_id,
            wallet_balance_after=result.wallet_balance_after,
            ledger_transaction_ref=result.ledger_transaction_id,
            already_exists=result.already_exists,
            table_session=result.table_session,
        )

    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult:
        _ensure_boxe_game_code(request.game_code)
        result = _settle_loss_in_process(
            cursor=request.cursor,
            user_id=request.player_ref,
            round_id=request.game_round_ref,
            safe_picks_count=request.successful_steps,
        )
        return PlatformSettlementResult(
            platform_round_ref=result.platform_round_id,
            wallet_balance_after=result.wallet_balance_after,
            ledger_transaction_ref=result.ledger_transaction_id,
            table_session=result.table_session,
        )


_DEFAULT_PLATFORM_ADAPTER: PlatformGameAdapter = InProcessBoxePlatformAdapter()


def get_default_platform_adapter() -> PlatformGameAdapter:
    return _DEFAULT_PLATFORM_ADAPTER


def _ensure_boxe_game_code(game_code: str) -> None:
    if game_code != GAME_CODE:
        raise BoxePlatformValidationError("BOXE platform adapter received the wrong game code")


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
            game_config={
                "rows": rows,
                "difficulty": difficulty,
            },
        )
    )
    return BoxePlatformRoundOpenResult(
        platform_round_id=result.platform_round_ref,
        wallet_account_id=result.wallet_account_ref,
        wallet_balance_after_start=result.wallet_balance_after_start,
        ledger_transaction_id=result.ledger_transaction_ref,
        table_session_id=result.table_session_ref,
        table_session=result.table_session,
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
    result = get_default_platform_adapter().settle_win(
        PlatformSettleWinRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=round_id,
            payout_amount=payout_amount,
            successful_steps=safe_picks_count,
            idempotency_key=idempotency_key,
        )
    )
    return BoxePlatformRoundSettlementResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        ledger_transaction_id=result.ledger_transaction_ref,
        already_exists=result.already_exists,
        table_session=result.table_session,
    )


def settle_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    round_id: str,
    safe_picks_count: int,
) -> BoxePlatformRoundSettlementResult:
    result = get_default_platform_adapter().settle_loss(
        PlatformSettleLossRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=round_id,
            successful_steps=safe_picks_count,
        )
    )
    return BoxePlatformRoundSettlementResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        ledger_transaction_id=result.ledger_transaction_ref,
        table_session=result.table_session,
    )


def _open_round_in_process(
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


def _settle_win_in_process(
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
            table_session=(
                dict(result["table_session"])
                if result.get("table_session") is not None
                else None
            ),
        )
    except PlatformRoundIdempotencyConflictError as exc:
        raise BoxePlatformIdempotencyConflictError(str(exc)) from exc
    except PlatformRoundValidationError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc


def _settle_loss_in_process(
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
            table_session=(
                dict(result["table_session"])
                if result.get("table_session") is not None
                else None
            ),
        )
    except PlatformRoundValidationError as exc:
        raise BoxePlatformValidationError(str(exc)) from exc
