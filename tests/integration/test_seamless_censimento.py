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

def test_censimento_rollback_missing_in_platform():
    # There is no cancel_round or rollback_round in PlatformGameAdapter
    from app.modules.platform.game_modules.adapter import PlatformGameAdapter
    
    methods = [m for m in dir(PlatformGameAdapter) if not m.startswith("_")]
    assert "open_round" in methods
    assert "settle_win" in methods
    assert "settle_loss" in methods
    # Prove rollback is missing
    assert "rollback_round" not in methods
    assert "cancel_round" not in methods

def test_censimento_open_round_db_requirements(db_helpers, db_connection):
    # What if we pass None to the service function for missing fields?
    with db_connection.cursor() as cursor:
        try:
            open_game_round(
                cursor=cursor,
                game_code="provider_x", # we can guess provider from HMAC
                user_id=None, # MISSING in ReserveRequest
                game_session_id=None, # MISSING in ReserveRequest
                idempotency_key="tx123",
                grid_size=0,
                mine_count=0,
                bet_amount=Decimal("10.0"),
                wallet_type=None, # MISSING
                title_code=None, # MISSING
                site_code=None, # MISSING
            )
            pytest.fail("Should have failed")
        except Exception as e:
            # We expect it to fail because user_id cannot be None, etc.
            assert "None" in str(e) or "null value in column" in str(e) or "argument" in str(e).lower()

