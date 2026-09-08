"""RIP-06 — each game adapter can return an open bet through the platform."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.games.boxe.platform_client import InProcessBoxePlatformAdapter
from app.modules.games.hi_lo.platform_client import InProcessHiLoPlatformAdapter
from app.modules.games.manichino.round_gateway import InProcessManichinoPlatformAdapter
from app.modules.games.mines.platform_client import InProcessMinesPlatformAdapter
from app.modules.platform.game_modules.adapter import (
    PlatformOpenRoundRequest,
    PlatformRollbackRoundRequest,
)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("adapter", "game_code", "title_code", "game_config"),
    [
        (InProcessMinesPlatformAdapter(), "mines", "mines001", {"grid_size": 9, "mine_count": 1}),
        (InProcessBoxePlatformAdapter(), "boxe", "boxe001", {"rows": 4, "difficulty": "easy"}),
        (InProcessHiLoPlatformAdapter(), "hi_lo", "hilo001", {"deck": "standard_52"}),
        (InProcessManichinoPlatformAdapter(), "manichino", "manichino_test", {"note": "rollback proof"}),
    ],
    ids=("mines", "boxe", "hi_lo", "manichino"),
)
def test_adapter_rollback_returns_the_open_bet_to_the_player(
    create_player,
    db_connection,
    db_helpers,
    adapter,
    game_code: str,
    title_code: str,
    game_config: dict[str, object],
) -> None:
    player = create_player(prefix=f"adapter-rollback-{game_code}")
    user_id = str(player["user_id"])
    round_id = str(uuid4())
    before = db_helpers.get_wallet_balance(user_id)

    with db_connection.transaction():
        with db_connection.cursor() as cursor:
            opened = adapter.open_round(
                PlatformOpenRoundRequest(
                    cursor=cursor,
                    game_code=game_code,
                    player_ref=user_id,
                    game_round_ref=round_id,
                    idempotency_key=f"adapter-open-{uuid4().hex}",
                    title_code=title_code,
                    site_code="casinoking",
                    wallet_source="cash",
                    bet_amount=Decimal("10.000000"),
                    game_config=game_config,
                )
            )
            assert opened.wallet_balance_after_start == Decimal(before) - Decimal("10.000000")
            rolled_back = adapter.rollback_round(
                PlatformRollbackRoundRequest(
                    cursor=cursor,
                    game_code=game_code,
                    player_ref=user_id,
                    game_round_ref=round_id,
                    idempotency_key=f"adapter-rollback-{uuid4().hex}",
                )
            )

    assert rolled_back.platform_round_ref == round_id
    assert rolled_back.wallet_balance_after == Decimal(before)
    assert db_helpers.get_wallet_balance(user_id) == before
