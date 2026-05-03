from decimal import Decimal

import psycopg

from app.modules.games.mines.platform_client import (
    InProcessPlatformGameClient,
    MinesPlatformRoundLossResult,
    MinesPlatformRoundOpenResult,
    MinesPlatformRoundWinResult,
    PlatformGameClient,
)

_platform_game_client: PlatformGameClient = InProcessPlatformGameClient()


def configure_platform_game_client(client: PlatformGameClient) -> None:
    """Override the platform boundary implementation.

    Fase 9a keeps the in-process client as the default. Future HTTP/contract
    tests can inject another implementation without changing Mines service
    code.
    """
    global _platform_game_client
    _platform_game_client = client


def get_platform_game_client() -> PlatformGameClient:
    return _platform_game_client


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

    Returns wallet_account_id, wallet_balance_after_start,
    ledger_transaction_id, table_session_id and the serialized table_session.
    """
    return _platform_game_client.open_round(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
        idempotency_key=idempotency_key,
        grid_size=grid_size,
        mine_count=mine_count,
        bet_amount=bet_amount,
        wallet_type=wallet_type,
        table_session_id=table_session_id,
        access_session_id=access_session_id,
    )


def get_existing_cashout_by_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    return _platform_game_client.get_existing_cashout_by_key(
        cursor=cursor,
        idempotency_key=idempotency_key,
    )


def get_cashout_snapshot(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
) -> dict[str, object] | None:
    return _platform_game_client.get_cashout_snapshot(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
    )


def build_cashout_idempotency_key(*, user_id: str, idempotency_key: str) -> str:
    return _platform_game_client.build_cashout_idempotency_key(
        user_id=user_id,
        idempotency_key=idempotency_key,
    )


def is_open_round_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return _platform_game_client.is_open_round_idempotency_violation(exc)


def is_settlement_idempotency_violation(exc: psycopg.errors.UniqueViolation) -> bool:
    return _platform_game_client.is_settlement_idempotency_violation(exc)


def get_round_start_snapshot(
    *,
    cursor: psycopg.Cursor,
    platform_round_id: str,
) -> dict[str, object]:
    return _platform_game_client.get_round_start_snapshot(
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
    return _platform_game_client.settle_win(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
        payout_amount=payout_amount,
        safe_reveals_count=safe_reveals_count,
        idempotency_key=idempotency_key,
    )


def settle_round_loss(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    game_round_id: str,
    safe_reveals_count: int,
) -> MinesPlatformRoundLossResult:
    return _platform_game_client.settle_loss(
        cursor=cursor,
        user_id=user_id,
        game_round_id=game_round_id,
        safe_reveals_count=safe_reveals_count,
    )
