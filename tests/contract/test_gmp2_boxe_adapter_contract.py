from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.games.boxe import platform_client
from app.modules.platform.game_modules.adapter import (
    GameEmbedDescriptor,
    GameLaunchDescriptor,
    GameReplayDescriptor,
    GameSessionDescriptor,
    GameStorageDescriptor,
    PlatformGameAdapter,
    PlatformOpenRoundRequest,
    PlatformOpenRoundResult,
    PlatformSettlementResult,
)


def test_gmp2_descriptor_interfaces_are_typed_and_host_neutral() -> None:
    launch = GameLaunchDescriptor(
        game_code="boxe",
        title_code="boxe001",
        site_code="casinoking",
        mode="demo",
        player_ref="player-1",
        wallet_source="demo",
    )
    session = GameSessionDescriptor(
        game_code="boxe",
        title_code="boxe001",
        site_code="casinoking",
        table_session_ref=None,
        access_session_ref=None,
    )
    storage = GameStorageDescriptor(
        namespace="host.example.game.boxe",
        allowed_uses=("audio_preferences", "ui_preferences"),
    )
    embed = GameEmbedDescriptor(protocol="ck-game-embed-v1", game_code="boxe")
    replay = GameReplayDescriptor(
        game_code="boxe",
        player_replay_endpoint="/games/boxe/round/{roundRef}/replay",
        admin_replay_endpoint="/games/boxe/admin/round/{roundRef}/replay",
        replay_payload_schema="boxe.replay.v1",
        viewer="module-owned",
    )

    assert launch.game_code == session.game_code == embed.game_code == replay.game_code == "boxe"
    assert storage.namespace.startswith("host.")
    assert "casinoking.access_token" not in storage.namespace


def test_boxe_in_process_adapter_satisfies_platform_adapter_protocol() -> None:
    assert isinstance(platform_client.InProcessBoxePlatformAdapter(), PlatformGameAdapter)


def test_boxe_open_round_uses_platform_adapter_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeAdapter()
    monkeypatch.setattr(platform_client, "get_default_platform_adapter", lambda: fake)

    result = platform_client.open_round(
        cursor=object(),  # type: ignore[arg-type]
        user_id="player-1",
        round_id="round-1",
        idempotency_key="open-1",
        rows=4,
        difficulty="easy",
        bet_amount=Decimal("1.000000"),
        wallet_type="cash",
        title_code="boxe001",
        site_code="casinoking",
        table_session_id="table-1",
        access_session_id="access-1",
    )

    assert isinstance(fake.open_request, PlatformOpenRoundRequest)
    assert fake.open_request.game_code == "boxe"
    assert fake.open_request.player_ref == "player-1"
    assert fake.open_request.game_round_ref == "round-1"
    assert fake.open_request.wallet_source == "cash"
    assert fake.open_request.game_config == {"rows": 4, "difficulty": "easy"}
    assert result.platform_round_id == "round-1"
    assert result.ledger_transaction_id == "ledger-open"


def test_boxe_settlement_uses_platform_adapter_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeAdapter()
    monkeypatch.setattr(platform_client, "get_default_platform_adapter", lambda: fake)

    win = platform_client.settle_win(
        cursor=object(),  # type: ignore[arg-type]
        user_id="player-1",
        round_id="round-1",
        payout_amount=Decimal("2.000000"),
        safe_picks_count=1,
        idempotency_key="cashout-1",
    )
    loss = platform_client.settle_loss(
        cursor=object(),  # type: ignore[arg-type]
        user_id="player-1",
        round_id="round-2",
        safe_picks_count=0,
    )

    assert fake.win_request is not None
    assert fake.win_request.game_code == "boxe"
    assert fake.win_request.payout_amount == Decimal("2.000000")
    assert fake.win_request.successful_steps == 1
    assert fake.win_request.idempotency_key == "cashout-1"
    assert win.ledger_transaction_id == "ledger-win"

    assert fake.loss_request is not None
    assert fake.loss_request.game_code == "boxe"
    assert fake.loss_request.game_round_ref == "round-2"
    assert fake.loss_request.successful_steps == 0
    assert loss.ledger_transaction_id == "ledger-loss"


class _FakeAdapter:
    def __init__(self) -> None:
        self.open_request = None
        self.win_request = None
        self.loss_request = None

    def open_round(self, request):
        self.open_request = request
        return PlatformOpenRoundResult(
            platform_round_ref=request.game_round_ref,
            wallet_account_ref="wallet-1",
            wallet_balance_after_start=Decimal("9.000000"),
            ledger_transaction_ref="ledger-open",
            table_session_ref="table-1",
            table_session={"id": "table-1"},
        )

    def settle_win(self, request):
        self.win_request = request
        return PlatformSettlementResult(
            platform_round_ref=request.game_round_ref,
            wallet_balance_after=Decimal("11.000000"),
            ledger_transaction_ref="ledger-win",
            already_exists=False,
            table_session={"id": "table-1"},
        )

    def settle_loss(self, request):
        self.loss_request = request
        return PlatformSettlementResult(
            platform_round_ref=request.game_round_ref,
            wallet_balance_after=Decimal("8.000000"),
            ledger_transaction_ref="ledger-loss",
            table_session={"id": "table-1"},
        )

