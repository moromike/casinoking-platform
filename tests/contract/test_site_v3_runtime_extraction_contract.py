from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
FRONTEND_V3 = ROOT / "frontend-v3"


GAMES = {
    "mines": {
        "route_path": "mines",
        "game_code": "mines",
        "standalone": "MinesStandalone",
        "v1_route": "frontend/app/mines/page.tsx",
        "v3_route": "frontend-v3/app/mines/page.tsx",
        "v1_entry": "frontend/app/ui/mines/mines-standalone.tsx",
    },
    "boxe": {
        "route_path": "boxe",
        "game_code": "boxe",
        "standalone": "BoxeStandalone",
        "v1_route": "frontend/app/boxe/page.tsx",
        "v3_route": "frontend-v3/app/boxe/page.tsx",
        "v1_entry": "frontend/app/ui/boxe/boxe-standalone.tsx",
    },
    "hi-lo": {
        "route_path": "hi-lo",
        "game_code": "hi_lo",
        "standalone": "HiLoStandalone",
        "v1_route": "frontend/app/hi-lo/page.tsx",
        "v3_route": "frontend-v3/app/hi-lo/page.tsx",
        "v1_entry": "frontend/app/ui/hi-lo/hi-lo-standalone.tsx",
    },
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_runtime_extraction_contract_document_exists_and_sets_target() -> None:
    contract = _read("docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md")

    assert "Status: ACTIVE" in contract
    assert "Default target for the first migration: `frontend-v3`." in contract
    assert "frontend-v3/app/runtime/{game}/page.tsx" in contract
    assert "Recommended order:" in contract
    assert "1. BOXE" in contract
    assert "No backend wallet, ledger, settlement, payout, RNG, fairness or game math" in contract
    for game in ["Mines", "BOXE", "HI-LO"]:
        assert game in contract


def test_site_v3_game_shells_still_wrap_v1_legacy_runtime_routes_until_migration() -> None:
    edge_conf = _read("infra/docker/edge.conf")
    game_frame = _read("frontend-v3/app/ui/game-frame-page.tsx")

    for game, config in GAMES.items():
        v3_route = _read(config["v3_route"])
        assert "GameFramePage" in v3_route
        assert f'gameCode: "{config["game_code"]}"' in v3_route
        assert f'routePath: "{config["route_path"]}"' in v3_route
        assert f"location /legacy-games/{game}" in edge_conf
        assert f"proxy_pass http://casinoking_frontend_v1/{config['route_path']};" in edge_conf

    assert 'return `/legacy-games/${config.routePath}?${params.toString()}`' in game_frame
    for param_name in ["mode", "wallet_source", "preview", "preview_token", "return_to"]:
        assert param_name in game_frame
    assert 'params.set("embed", "1")' in game_frame
    assert 'params.set("embed_origin", origin)' in game_frame
    assert "GAME_EMBED_CLOSE_MESSAGE" in game_frame
    assert "GAME_EMBED_FULLSCREEN_STATE_MESSAGE" in game_frame


def test_v1_direct_game_routes_are_runtime_entrypoints_not_public_shells() -> None:
    for config in GAMES.values():
        route_source = _read(config["v1_route"])
        entry_source = _read(config["v1_entry"])
        assert config["standalone"] in route_source
        assert "GameFramePage" not in route_source
        assert "PlayerShell" not in route_source
        assert "useGameLaunchContext" in entry_source
        assert "useGameEmbedBridge" in entry_source
        assert "GameBootShell" in entry_source
        assert 'window.location.assign(returnTo ?? "/")' in entry_source


def test_runtime_storage_and_embed_contract_cover_all_current_games() -> None:
    storage = _read("frontend/app/ui/game-runtime/game-storage.ts")
    boot_request = _read("frontend/app/ui/game-runtime/game-boot-request.ts")
    embed_bridge = _read("frontend/app/ui/game-runtime/use-game-embed-bridge.ts")

    assert 'export const ALLOWED_GAME_NAMESPACES = ["mines", "boxe", "hi_lo"] as const;' in storage
    for namespace in ["mines", "boxe", "hi_lo"]:
        assert namespace in storage

    assert "returnTo: string | null" in boot_request
    assert 'sanitizeAuthReturnTo(searchParams.get("return_to"))' in boot_request
    assert 'searchParams.get("embed") === "1"' in boot_request
    assert "readGameBootWalletSource" in boot_request

    assert 'GAME_EMBED_CLOSE_MESSAGE = "casinoking:game-close"' in embed_bridge
    assert 'GAME_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:game-fullscreen-state"' in embed_bridge
    assert 'new URLSearchParams(window.location.search).get("embed_origin")' in embed_bridge
    assert "window.parent.postMessage" in embed_bridge
