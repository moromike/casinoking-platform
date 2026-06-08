from decimal import Decimal

import psycopg

from app.modules.platform.game_modules.adapter import (
    PlatformOpenRoundRequest,
    PlatformSettleLossRequest,
    PlatformSettleWinRequest,
)

from app.modules.games.mines.platform_client import (
    MinesPlatformRoundLossResult,
    MinesPlatformRoundOpenResult,
    MinesPlatformRoundWinResult,
    PlatformGameAdapter,
    get_default_platform_adapter,
    get_existing_cashout_by_key as _get_existing_cashout_by_key,
    get_cashout_snapshot as _get_cashout_snapshot,
    build_cashout_idempotency_key as _build_cashout_idempotency_key,
    is_open_round_idempotency_violation as _is_open_round_idempotency_violation,
    is_settlement_idempotency_violation as _is_settlement_idempotency_violation,
    get_round_start_snapshot as _get_round_start_snapshot,
)

_platform_adapter: PlatformGameAdapter = get_default_platform_adapter()


def configure_platform_game_client(client: PlatformGameAdapter) -> None:
    """Override the platform boundary implementation.

    Fase 9a keeps the in-process adapter as the default. Future HTTP/contract
    tests can inject another implementation without changing Mines service
    code.
    """
    global _platform_adapter
    _platform_adapter = client


def get_platform_game_client() -> PlatformGameAdapter:
    return _platform_adapter


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
    """Open the platform-owned economic round for a Mines game round.

    Returns wallet_account_id, wallet_balance_after_start,
    ledger_transaction_id, table_session_id and the serialized table_session.
    """
    result = _platform_adapter.open_round(
        PlatformOpenRoundRequest(
            cursor=cursor,
            game_code="mines",
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


def get_existing_cashout_by_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    return _get_existing_cashout_by_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )


def get_cashout_snapshot(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
) -> dict[str, object] | None:
    return _get_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
    )


def build_cashout_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return _build_cashout_idempotency_key(
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def is_open_round_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return _is_open_round_idempotency_violation(exc)


def is_settlement_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return _is_settlement_idempotency_violation(exc)


def get_round_start_snapshot(
    *,
    cursor: psycopg.Cursor,
    platform_round_id: str,
) -> dict[str, object]:
    return _get_round_start_snapshot(
        cursor=cursor,
        platform_round_id=platform_round_id,
    )


def settle_round_win(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    payout_amount: Decimal,
    safe_reveals_count: int,
    idempotency_key: str,
) -> MinesPlatformRoundWinResult:
    result = _platform_adapter.settle_win(
        PlatformSettleWinRequest(
            cursor=cursor,
            game_code="mines",
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


def settle_round_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    safe_reveals_count: int,
) -> MinesPlatformRoundLossResult:
    result = _platform_adapter.settle_loss(
        PlatformSettleLossRequest(
            cursor=cursor,
            game_code="mines",
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

# Re-export platform boundary symbols so service.py stays gateway-clean.
from app.modules.platform.demo_wallet.service import (
    DemoWalletIdempotencyConflictError,
    DemoWalletInsufficientBalanceError,
    DemoWalletValidationError,
    credit_for_win,
    debit_for_bet,
    open_demo_session,
    record_loss,
)
from app.modules.platform.table_sessions.service import TableSessionStateConflictError
