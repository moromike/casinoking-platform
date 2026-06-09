from __future__ import annotations

from app.modules.platform.game_modules.descriptors import (
    EMBED_PROTOCOL_V1,
    STORAGE_ALLOWED_USES,
    build_replay_descriptor,
)
from app.modules.platform.game_modules.manifest import (
    GameModuleManifestNotFoundError,
    get_game_module_manifest,
    serialize_game_module_manifest,
)


def test_gmp5_boxe_manifest_declares_package_first_boundary() -> None:
    manifest = serialize_game_module_manifest(get_game_module_manifest("boxe"))

    assert manifest["manifest_version"] == 1
    assert manifest["game_code"] == "boxe"
    assert manifest["display_name"] == "BOXE"
    assert manifest["runtime"]["entry"] == "/runtime/boxe"
    assert manifest["runtime"]["embed_protocol"] == EMBED_PROTOCOL_V1
    assert manifest["runtime"]["frontend_package_ready"] is False
    assert manifest["backend"]["adapter_mode"] == "in_process_v1"
    assert manifest["backend"]["launch_token_endpoint"] == "/games/boxe/launch-token"
    assert manifest["backend"]["launch_token_modes"] == ("real",)
    assert manifest["backend"]["launch_token_optional_actions"] == ("start",)
    assert manifest["backend"]["launch_token_required_actions"] == ()
    assert manifest["backend"]["token_authoritative_fields"] == (
        "title_code",
        "site_code",
        "game_code",
        "mode",
    )
    assert manifest["backend"]["legacy_no_token_start_supported"] is True
    assert manifest["backend"]["service_ready"] is False
    assert manifest["admin"]["arbitrary_code_allowed"] is False
    assert manifest["host_integration"]["selected_target"] == "same_repo_manifest_first"
    assert manifest["host_integration"]["physical_split"] == "none"
    assert manifest["host_integration"]["mock_host_ready"] is True
    assert manifest["host_integration"]["next_gate"] == "consume-launch-descriptor-in-runtime-actions"


def test_gmp5_boxe_manifest_matches_descriptor_contracts() -> None:
    manifest = serialize_game_module_manifest(get_game_module_manifest("boxe"))
    replay = build_replay_descriptor(game_code="boxe")

    assert manifest["storage"]["namespace_from_launch_descriptor"] is True
    assert manifest["storage"]["allowed_uses"] == STORAGE_ALLOWED_USES
    assert manifest["reporting"]["player_replay_endpoint"] == replay.player_replay_endpoint
    assert manifest["reporting"]["admin_replay_endpoint"] == replay.admin_replay_endpoint
    assert manifest["reporting"]["replay_payload_schema"] == replay.replay_payload_schema
    assert manifest["reporting"]["viewer"] == replay.viewer
    assert manifest["reporting"]["account_summary_fields"] == replay.account_summary_fields
    assert manifest["reporting"]["finance_summary_fields"] == replay.finance_summary_fields


def test_gmp5_boxe_manifest_declares_assets_i18n_and_no_arbitrary_code() -> None:
    manifest = serialize_game_module_manifest(get_game_module_manifest("boxe"))

    asset_kinds = {asset["kind"]: asset for asset in manifest["assets"]}
    assert {
        "game_card",
        "symbol_safe",
        "symbol_mine",
        "title_logo",
        "game_area_background",
        "audio_safe_reveal",
        "audio_mine_hit",
        "audio_collect",
        "audio_win",
    }.issubset(asset_kinds)
    assert asset_kinds["game_card"]["render_mode"] == "cover"
    assert asset_kinds["symbol_safe"]["render_mode"] == "contain"
    assert asset_kinds["audio_collect"]["render_mode"] == "audio"
    assert manifest["i18n"]["locales"] == ("it", "en", "de", "es")
    assert manifest["i18n"]["default_locale"] == "it"
    assert manifest["admin"]["arbitrary_code_allowed"] is False
    assert "executable" not in str(manifest).lower()


def test_gmp5_manifest_is_explicit_about_current_blockers() -> None:
    manifest = serialize_game_module_manifest(get_game_module_manifest("boxe"))
    blockers = " ".join(
        [
            *manifest["backend"]["service_split_blockers"],
            *manifest["host_integration"]["known_blockers"],
        ]
    )

    assert "psycopg.Cursor" in blockers
    assert "X-Game-Launch-Token" in blockers
    assert "CasinoKing-oriented" in blockers
    assert "frontend_package_ready" in str(manifest)
    assert manifest["runtime"]["consumes_host_storage_namespace"] is False
    assert manifest["runtime"]["consumes_neutral_embed_protocol"] is False


def test_gmp5_unknown_manifest_has_no_fallback() -> None:
    try:
        get_game_module_manifest("unknown")
    except GameModuleManifestNotFoundError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("Unknown game module manifest must not fallback to BOXE")
