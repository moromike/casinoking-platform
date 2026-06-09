import pathlib
import re


GAME_STORAGE_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "frontend-v3"
    / "app"
    / "ui"
    / "game-runtime"
    / "game-storage.ts"
)


def _source() -> str:
    return GAME_STORAGE_PATH.read_text(encoding="utf-8")


def test_game_storage_whitelists_current_runtime_namespaces():
    source = _source()

    assert 'export const ALLOWED_GAME_NAMESPACES = ["mines", "boxe", "hi_lo"] as const;' in source
    assert 'export const MINES_GAME_STORAGE_NAMESPACE: GameStorageNamespace = "mines";' in source
    assert 'export const BOXE_GAME_STORAGE_NAMESPACE: GameStorageNamespace = "boxe";' in source
    assert 'export const HI_LO_GAME_STORAGE_NAMESPACE: GameStorageNamespace = "hi_lo";' in source


def test_game_storage_rejects_non_whitelisted_namespaces():
    source = _source()

    assert "Unsupported game storage namespace" in source
    assert "isAllowedGameStorageNamespace" in source
    assert re.search(r"if \(!isAllowedGameStorageNamespace\(namespace\)\)", source)


def test_game_storage_keeps_legacy_mines_keys_backward_compatible():
    source = _source()

    expected_keys = {
        "casinoking.access_token",
        "casinoking.email",
        "casinoking.current_session_id",
        "casinoking.mines_launch_token",
        "casinoking.mines_launch_token_expires_at",
        "casinoking.mines_launch_title_code",
        "ck_demo_anon_token",
        "ck_demo_game_launch_token",
        "ck_demo_game_launch_token_expires_at",
        "ck_demo_game_launch_title_code",
        "ck_demo_chip_balance",
        "casinoking.mines_table_session_id",
    }

    for key in expected_keys:
        assert key in source


def test_game_storage_uses_distinct_boxe_runtime_keys():
    source = _source()

    expected_keys = {
        "casinoking.boxe_current_session_id",
        "casinoking.boxe_launch_token",
        "casinoking.boxe_launch_token_expires_at",
        "casinoking.boxe_launch_title_code",
        "ck_boxe_demo_anon_token",
        "ck_boxe_demo_game_launch_token",
        "ck_boxe_demo_game_launch_token_expires_at",
        "ck_boxe_demo_game_launch_title_code",
        "ck_boxe_demo_chip_balance",
        "casinoking.boxe_table_session_id",
    }

    for key in expected_keys:
        assert key in source


def test_game_storage_uses_distinct_hi_lo_runtime_keys():
    source = _source()

    expected_keys = {
        "casinoking.hi_lo_current_session_id",
        "casinoking.hi_lo_launch_token",
        "casinoking.hi_lo_launch_token_expires_at",
        "casinoking.hi_lo_launch_title_code",
        "ck_hi_lo_demo_anon_token",
        "ck_hi_lo_demo_game_launch_token",
        "ck_hi_lo_demo_game_launch_token_expires_at",
        "ck_hi_lo_demo_game_launch_title_code",
        "ck_hi_lo_demo_chip_balance",
        "casinoking.hi_lo_table_session_id",
    }

    for key in expected_keys:
        assert key in source

