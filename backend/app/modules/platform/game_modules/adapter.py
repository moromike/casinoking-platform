from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Mapping, Protocol, runtime_checkable

import psycopg


@dataclass(frozen=True)
class GameLaunchDescriptor:
    game_code: str
    title_code: str
    site_code: str
    mode: str
    player_ref: str
    wallet_source: str
    launch_ref: str | None = None
    host_code: str | None = None
    brand_code: str | None = None
    return_url: str | None = None
    locale: str | None = None
    embed_origin: str | None = None
    storage_namespace: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class GameSessionDescriptor:
    game_code: str
    title_code: str
    site_code: str
    table_session_ref: str | None
    access_session_ref: str | None


@dataclass(frozen=True)
class GameStorageDescriptor:
    namespace: str
    game_code: str | None = None
    title_code: str | None = None
    site_code: str | None = None
    allowed_uses: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameEmbedDescriptor:
    protocol: str
    game_code: str
    launch_ref: str | None = None
    embed_origin: str | None = None


@dataclass(frozen=True)
class GameReplayDescriptor:
    game_code: str
    player_replay_endpoint: str
    admin_replay_endpoint: str
    replay_payload_schema: str
    viewer: str
    account_summary_fields: tuple[str, ...] = ()
    finance_summary_fields: tuple[str, ...] = ()
    retention: str = "host-policy"


@dataclass(frozen=True)
class PlatformOpenRoundRequest:
    cursor: psycopg.Cursor
    game_code: str
    player_ref: str
    game_round_ref: str
    idempotency_key: str
    title_code: str
    site_code: str
    wallet_source: str
    bet_amount: Decimal
    table_session_ref: str | None = None
    access_session_ref: str | None = None
    game_config: Mapping[str, object] = field(default_factory=dict)
    correlation_id: str | None = None


@dataclass(frozen=True)
class PlatformOpenRoundResult:
    platform_round_ref: str
    wallet_account_ref: str
    wallet_balance_after_start: Decimal
    ledger_transaction_ref: str
    table_session_ref: str
    table_session: dict[str, object]


@dataclass(frozen=True)
class PlatformSettleWinRequest:
    cursor: psycopg.Cursor
    game_code: str
    player_ref: str
    game_round_ref: str
    payout_amount: Decimal
    successful_steps: int
    idempotency_key: str
    replay_ref: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class PlatformSettleLossRequest:
    cursor: psycopg.Cursor
    game_code: str
    player_ref: str
    game_round_ref: str
    successful_steps: int
    replay_ref: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class PlatformSettlementResult:
    platform_round_ref: str
    wallet_balance_after: Decimal
    ledger_transaction_ref: str
    already_exists: bool = False
    table_session: dict[str, object] | None = None


@runtime_checkable
class PlatformGameAdapter(Protocol):
    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult:
        ...

    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult:
        ...

    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult:
        ...
