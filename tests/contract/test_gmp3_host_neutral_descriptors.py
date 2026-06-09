from app.modules.platform.game_modules.descriptors import (
    EMBED_PROTOCOL_V1,
    build_game_module_descriptor_payload,
    build_storage_namespace,
)


def test_gmp3_storage_namespace_is_host_and_game_scoped_without_brand_assumption() -> None:
    namespace = build_storage_namespace(site_code="Arcade Lab", game_code="BOXE")

    assert namespace == "host.arcade-lab.game.boxe"
    assert "casinoking" not in namespace


def test_gmp3_launch_payload_exposes_host_neutral_descriptors() -> None:
    payload = build_game_module_descriptor_payload(
        game_code="boxe",
        title_code="boxe001",
        site_code="arcade_lab",
        mode="demo",
        player_ref="anonymous-player",
        wallet_source="demo",
        launch_ref="launch-123",
        host_code="mockhost",
        brand_code="arcade_lab",
        return_url="https://arcade.example/return",
        locale="en",
        embed_origin="https://arcade.example",
        correlation_id="corr-123",
    )

    launch = payload["launch_descriptor"]
    storage = payload["storage_descriptor"]
    embed = payload["embed_descriptor"]
    replay = payload["replay_descriptor"]

    assert launch["host_code"] == "mockhost"
    assert launch["brand_code"] == "arcade_lab"
    assert launch["site_code"] == "arcade_lab"
    assert launch["storage_namespace"] == "host.arcade_lab.game.boxe"
    assert storage["namespace"] == "host.arcade_lab.game.boxe"
    assert storage["allowed_uses"] == (
        "ui_preferences",
        "audio_preferences",
        "safe_resume_hints",
        "demo_anonymous_convenience",
    )
    assert embed["protocol"] == EMBED_PROTOCOL_V1
    assert replay["game_code"] == "boxe"
    assert replay["player_replay_endpoint"] == "/games/boxe/round/{roundRef}/replay"
    assert "casinoking" not in str(payload).lower()
