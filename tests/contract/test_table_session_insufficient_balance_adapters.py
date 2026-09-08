from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.games.boxe import platform_client as boxe_platform_client
from app.modules.games.hi_lo import platform_client as hi_lo_platform_client
from app.modules.games.manichino import round_gateway as manichino_round_gateway
from app.modules.games.mines import platform_client as mines_platform_client
from app.modules.games.boxe.platform_client import BoxePlatformInsufficientBalanceError
from app.modules.games.hi_lo.platform_client import HiLoPlatformInsufficientBalanceError
from app.modules.games.manichino.exceptions import ManichinoInsufficientBalanceError
from app.modules.games.mines.exceptions import MinesInsufficientBalanceError
from app.modules.platform.game_modules.adapter import PlatformOpenRoundRequest
from app.modules.platform.table_sessions.service import TableSessionInsufficientBalanceError


@pytest.mark.parametrize(
    ("adapter", "module", "game_code", "game_config", "expected_error"),
    [
        (
            mines_platform_client.InProcessMinesPlatformAdapter(),
            mines_platform_client,
            "mines",
            {"grid_size": 25, "mine_count": 3},
            MinesInsufficientBalanceError,
        ),
        (
            boxe_platform_client.InProcessBoxePlatformAdapter(),
            boxe_platform_client,
            "boxe",
            {"rows": 4, "difficulty": "easy"},
            BoxePlatformInsufficientBalanceError,
        ),
        (
            hi_lo_platform_client.InProcessHiLoPlatformAdapter(),
            hi_lo_platform_client,
            "hi_lo",
            {"deck": "standard_52"},
            HiLoPlatformInsufficientBalanceError,
        ),
        (
            manichino_round_gateway.InProcessManichinoPlatformAdapter(),
            manichino_round_gateway,
            "manichino",
            {"note": "esito deciso dal chiamante"},
            ManichinoInsufficientBalanceError,
        ),
    ],
)
def test_game_adapters_translate_table_session_insufficient_balance(
    monkeypatch: pytest.MonkeyPatch,
    adapter: object,
    module: object,
    game_code: str,
    game_config: dict[str, object],
    expected_error: type[Exception],
) -> None:
    def raise_insufficient_balance(**_kwargs: object) -> object:
        raise TableSessionInsufficientBalanceError("Table session amount exceeds available balance")

    monkeypatch.setattr(module, "open_game_round", raise_insufficient_balance)
    request = PlatformOpenRoundRequest(
        cursor=object(),  # type: ignore[arg-type]
        game_code=game_code,
        player_ref="player-1",
        game_round_ref="round-1",
        idempotency_key="open-1",
        title_code=f"{game_code}_test",
        site_code="casinoking",
        wallet_source="cash",
        bet_amount=Decimal("1.000000"),
        table_session_ref="table-1",
        game_config=game_config,
    )

    with pytest.raises(expected_error, match="available balance"):
        adapter.open_round(request)  # type: ignore[union-attr]
