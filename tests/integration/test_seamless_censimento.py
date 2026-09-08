import pytest
import psycopg
from decimal import Decimal
from pydantic import ValidationError
from typing import Any

from app.modules.platform.game_modules.adapter import PlatformOpenRoundRequest
from app.modules.platform.rounds.service import open_game_round

def test_censimento_reserve_requirements():
    # ReserveRequest only gives tx_id and amount.
    tx_id = "tx123"
    amount = Decimal("10.0")

    # If we try to create a PlatformOpenRoundRequest with only these:
    try:
        req = PlatformOpenRoundRequest(
            cursor=None, # type: ignore
            idempotency_key=tx_id,
            bet_amount=amount,
            # we omit the others to see it fail
        )
        pytest.fail("Should have raised TypeError for missing arguments")
    except TypeError as e:
        msg = str(e)
        assert "game_code" in msg
        assert "player_ref" in msg
        assert "game_round_ref" in msg
        assert "title_code" in msg
        assert "site_code" in msg
        assert "wallet_source" in msg

def test_censimento_platform_adapter_exposes_reachable_rollback():
    """RIP-04: rollback is a platform capability, not a missing-method census."""
    from app.modules.platform.game_modules.adapter import PlatformGameAdapter
    
    methods = [m for m in dir(PlatformGameAdapter) if not m.startswith("_")]
    assert "open_round" in methods
    assert "settle_win" in methods
    assert "settle_loss" in methods
    assert "rollback_round" in methods
    assert "cancel_round" not in methods

def test_censimento_open_round_rejects_unknown_engine_before_any_write(
    create_player, db_helpers, db_connection
):
    """RIP-04: invalid engine input is rejected before a wallet or round write."""
    player = create_player(prefix="censimento-invalid-engine")
    user_id = str(player["user_id"])
    before = db_helpers.get_wallet_balance(user_id)
    with db_connection.cursor() as cursor:
        with pytest.raises(Exception, match="Game engine not found"):
            open_game_round(
                cursor=cursor,
                game_code="provider_x",
                user_id=user_id,
                game_session_id="censimento-invalid-engine-round",
                idempotency_key="censimento-invalid-engine",
                grid_size=0,
                mine_count=0,
                bet_amount=Decimal("10.0"),
                wallet_type="cash",
                title_code="mines_classic",
                site_code="casinoking",
            )
    assert db_helpers.get_wallet_balance(user_id) == before
