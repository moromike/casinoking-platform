from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import psycopg

from app.modules.games.mines.exceptions import (
    MinesIdempotencyConflictError,
    MinesInsufficientBalanceError,
    MinesValidationError,
)
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
    get_existing_round_win_by_key,
    get_game_round_cashout_snapshot,
    is_game_round_open_idempotency_violation,
    is_game_round_settlement_idempotency_violation,
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

GAME_CODE = "mines"


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


class InProcessMinesPlatformAdapter:
    """Mines adapter over the current in-process platform services."""

    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult:
        _ensure_mines_game_code(request.game_code)
        try:
            result = open_game_round(
                cursor=request.cursor,
                game_code=GAME_CODE,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
                idempotency_key=request.idempotency_key,
                grid_size=int(request.game_config.get("grid_size", 25)),
                mine_count=int(request.game_config.get("mine_count", 3)),
                bet_amount=request.bet_amount,
                wallet_type=request.wallet_source,
                table_session_id=request.table_session_ref,
                access_session_id=request.access_session_ref,
                title_code=request.title_code,
                site_code=request.site_code,
                request_fingerprint=request.request_fingerprint,
                game_config_payload=dict(request.game_config),
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

        return PlatformOpenRoundResult(
            platform_round_ref=str(result["platform_round_id"]),
            wallet_account_ref=str(result["wallet_account_id"]),
            wallet_balance_after_start=Decimal(result["wallet_balance_after_start"]),
            ledger_transaction_ref=str(result["ledger_transaction_id"]),
            table_session_ref=str(result["table_session_id"]),
            table_session=dict(result["table_session"]),
        )

    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult:
        _ensure_mines_game_code(request.game_code)
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
        except PlatformRoundValidationError as exc:
            raise MinesValidationError(str(exc)) from exc
        except PlatformRoundIdempotencyConflictError as exc:
            raise MinesIdempotencyConflictError(str(exc)) from exc

        wallet_balance_after = result.get("wallet_balance_after")
        if wallet_balance_after is None:
            snapshot = get_game_round_cashout_snapshot(
                cursor=request.cursor,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
            )
            if snapshot is None:
                raise RuntimeError("Cashout snapshot is not available")
            wallet_balance_after = snapshot["wallet_balance_after"]

        return PlatformSettlementResult(
            platform_round_ref=str(result.get("platform_round_id", request.game_round_ref)),
            wallet_balance_after=Decimal(wallet_balance_after),
            ledger_transaction_ref=str(result["ledger_transaction_id"]),
            already_exists=bool(result["already_exists"]),
        )

    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult:
        _ensure_mines_game_code(request.game_code)
        try:
            result = settle_game_round_loss(
                cursor=request.cursor,
                game_code=GAME_CODE,
                user_id=request.player_ref,
                game_session_id=request.game_round_ref,
                safe_reveals_count=request.successful_steps,
            )
        except PlatformRoundValidationError as exc:
            raise MinesValidationError(str(exc)) from exc

        return PlatformSettlementResult(
            platform_round_ref=str(result.get("platform_round_id", request.game_round_ref)),
            wallet_balance_after=Decimal(result["wallet_balance_after"]),
            ledger_transaction_ref=str(result["bet_transaction_id"]),
        )


_DEFAULT_PLATFORM_ADAPTER: PlatformGameAdapter = InProcessMinesPlatformAdapter()


def get_default_platform_adapter() -> PlatformGameAdapter:
    return _DEFAULT_PLATFORM_ADAPTER


# ---------------------------------------------------------------------------
# Core wrappers (use typed adapter)
# ---------------------------------------------------------------------------


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
    title_code: str | None = None,
    site_code: str | None = None,
    request_fingerprint: str | None = None,
) -> MinesPlatformRoundOpenResult:
    result = get_default_platform_adapter().open_round(
        PlatformOpenRoundRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=game_round_id,
            idempotency_key=idempotency_key,
            title_code=title_code,
            site_code=site_code,
            wallet_source=wallet_type,
            bet_amount=bet_amount,
            table_session_ref=table_session_id,
            access_session_ref=access_session_id,
            request_fingerprint=request_fingerprint,
            game_config={
                "grid_size": grid_size,
                "mine_count": mine_count,
            },
        )
    )
    return MinesPlatformRoundOpenResult(
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
    game_round_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
) -> MinesPlatformRoundWinResult:
    result = get_default_platform_adapter().settle_win(
        PlatformSettleWinRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=game_round_id,
            payout_amount=payout_amount,
            successful_steps=safe_reveals_count,
            idempotency_key=idempotency_key,
        )
    )
    return MinesPlatformRoundWinResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        ledger_transaction_id=result.ledger_transaction_ref,
        already_exists=result.already_exists,
    )


def settle_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    safe_reveals_count: int,
) -> MinesPlatformRoundLossResult:
    result = get_default_platform_adapter().settle_loss(
        PlatformSettleLossRequest(
            cursor=cursor,
            game_code=GAME_CODE,
            player_ref=user_id,
            game_round_ref=game_round_id,
            successful_steps=safe_reveals_count,
        )
    )
    return MinesPlatformRoundLossResult(
        platform_round_id=result.platform_round_ref,
        wallet_balance_after=result.wallet_balance_after,
        bet_transaction_id=result.ledger_transaction_ref,
        safe_reveals_count=safe_reveals_count,
    )


# ---------------------------------------------------------------------------
# Extra helpers (direct functions, not part of PlatformGameAdapter)
# ---------------------------------------------------------------------------


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
    return get_game_round_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_session_id=game_round_id,
    )


def build_cashout_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return namespace_game_round_win_idempotency_key(
        game_code=GAME_CODE,
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def is_open_round_idempotency_violation(
    exc: psycopg.errors.UniqueViolation,
) -> bool:
    return is_game_round_open_idempotency_violation(exc)


def is_settlement_idempotency_violation(
    exc: psycopg.errors.UniqueViolation,
) -> bool:
    return is_game_round_settlement_idempotency_violation(exc)


def get_round_start_snapshot(
    *,
    cursor: psycopg.Cursor,
    platform_round_id: str,
) -> dict[str, object]:
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


def _ensure_mines_game_code(game_code: str) -> None:
    if game_code != GAME_CODE:
        raise MinesValidationError("Mines platform adapter received the wrong game code")
