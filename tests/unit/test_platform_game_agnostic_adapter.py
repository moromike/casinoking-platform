import pytest

from app.modules.platform import game_codes
from app.modules.platform.game_launch import service as game_launch_service
from app.modules.platform.rounds import service as rounds_service
from app.modules.platform.table_sessions import service as table_sessions_service


def test_platform_allowed_game_codes_include_mines_boxe_and_hi_lo() -> None:
    assert game_codes.ALLOWED_GAME_CODES == ("mines", "boxe", "hi_lo")


def test_game_round_idempotency_key_is_namespaced_by_game_code() -> None:
    assert (
        rounds_service.namespace_game_round_win_idempotency_key(
            game_code="boxe",
            user_id="player-1",
            idempotency_key="cashout-1",
        )
        == "boxe:cashout:player-1:cashout-1"
    )


def test_removed_mines_specific_round_api_names_are_not_exported() -> None:
    removed_names = [
        "open_" + "mines_round",
        "settle_" + "mines_round_win",
        "settle_" + "mines_round_loss",
        "namespace_" + "mines_round_win_idempotency_key",
    ]
    for name in removed_names:
        assert not hasattr(rounds_service, name)


def test_game_launch_accepts_whitelisted_boxe(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_published_title_for_launch(*, site_code: str, title_code: str) -> dict[str, object]:
        return {
            "engine_code": "boxe",
            "is_master": False,
            "publication": {
                "lobby_visibility": "visible",
                "demo_enabled": True,
                "real_enabled": True,
            },
        }

    monkeypatch.setattr(
        game_launch_service,
        "get_published_title_for_launch",
        fake_get_published_title_for_launch,
    )

    token = game_launch_service.issue_game_launch_token(
        player_id="player-1",
        role="player",
        game_code="boxe",
        title_code="boxe001",
        site_code="casinoking",
        mode="real",
    )

    assert token["game_code"] == "boxe"
    assert token["title_code"] == "boxe001"


def test_game_launch_accepts_whitelisted_hi_lo(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_published_title_for_launch(*, site_code: str, title_code: str) -> dict[str, object]:
        return {
            "engine_code": "hi_lo",
            "is_master": False,
            "publication": {
                "lobby_visibility": "visible",
                "demo_enabled": True,
                "real_enabled": True,
            },
        }

    monkeypatch.setattr(
        game_launch_service,
        "get_published_title_for_launch",
        fake_get_published_title_for_launch,
    )

    token = game_launch_service.issue_game_launch_token(
        player_id="player-1",
        role="player",
        game_code="hi_lo",
        title_code="hilo001",
        site_code="casinoking",
        mode="real",
    )

    assert token["game_code"] == "hi_lo"
    assert token["title_code"] == "hilo001"


def test_game_launch_rejects_non_whitelisted_game_code() -> None:
    with pytest.raises(game_launch_service.GameLaunchTokenValidationError):
        game_launch_service.issue_game_launch_token(
            player_id="player-1",
            role="player",
            game_code="slots",
            title_code="slots001",
            site_code="casinoking",
            mode="real",
        )


@pytest.mark.parametrize(
    "validator_name",
    [
        "validate_optional_game_launch_token_for_player",
        "validate_required_game_launch_token_for_player",
    ],
)
def test_player_launch_validation_rejects_demo_context_without_keyerror(
    monkeypatch: pytest.MonkeyPatch,
    validator_name: str,
) -> None:
    def fake_validate_game_launch_token(*, game_launch_token: str) -> dict[str, object]:
        assert game_launch_token == "demo-token"
        return {
            "game_code": "boxe",
            "title_code": "boxe001",
            "site_code": "casinoking",
            "mode": "demo",
            "anonymous_id": "anon-1",
        }

    monkeypatch.setattr(
        game_launch_service,
        "validate_game_launch_token",
        fake_validate_game_launch_token,
    )

    validator = getattr(game_launch_service, validator_name)
    with pytest.raises(game_launch_service.GameLaunchTokenOwnershipError):
        validator(game_launch_token="demo-token", player_id="player-1")


def test_table_session_game_code_normalization_accepts_boxe_hi_lo_and_rejects_slots() -> None:
    assert table_sessions_service._normalize_game_code(" BOXE ") == "boxe"
    assert table_sessions_service._normalize_game_code(" HI_LO ") == "hi_lo"
    with pytest.raises(table_sessions_service.TableSessionValidationError):
        table_sessions_service._normalize_game_code("slots")
