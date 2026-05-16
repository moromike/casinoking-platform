from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest


playwright = pytest.importorskip("playwright.sync_api")


def _find_chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


@pytest.mark.integration
def test_player_lobby_renders_game_card_asset_from_library_payload(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    library_payload = {
        "success": True,
        "data": {
            "site": {
                "site_code": "casinoking",
                "display_name": "CasinoKing",
                "status": "active",
            },
            "titles": [
                {
                    "title_code": "mines_card_test",
                    "engine_code": "mines",
                    "engine_display_name": "Mines",
                    "display_name": "Mines Card Test",
                    "catalog_display_name": "Mines Card Test",
                    "description": "Card image smoke.",
                    "demo_enabled": True,
                    "real_enabled": True,
                    "featured": False,
                    "position": 1,
                    "game_card_asset": {
                        "id": "asset-game-card",
                        "asset_kind": "game_card",
                        "public_url": "/static/games/mines_card_test/game_card/card.png",
                        "mime": "image/png",
                        "byte_size": 1024,
                        "created_at": "2026-05-16T00:00:00+00:00",
                    },
                }
            ],
        },
    }
    home_payload = {
        "success": True,
        "data": {
            "site": {
                "site_code": "casinoking",
                "display_name": "CasinoKing",
                "status": "active",
            },
            "slots": [],
        },
    }

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1015, "height": 768})
        page.route(
            "**/api/v1/games/library*",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(library_payload),
            ),
        )
        page.route(
            "**/api/v1/site/home*",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(home_payload),
            ),
        )

        page.goto(frontend_base_url, wait_until="networkidle")
        page.get_by_role("heading", name="Mines Card Test").wait_for()

        art_metrics = page.locator(".player-lobby-card-art.has-game-card").evaluate(
            """
            (element) => ({
              backgroundImage: window.getComputedStyle(element).backgroundImage,
              fallbackCopyCount: element.querySelectorAll('.player-lobby-art-copy, .player-lobby-board').length,
            })
            """
        )

        assert "/static/games/mines_card_test/game_card/card.png" in art_metrics["backgroundImage"]
        assert art_metrics["fallbackCopyCount"] == 0
        assert page.get_by_role("link", name="Demo").is_visible()
        assert page.get_by_role("link", name="Log in to play").is_visible()

        browser.close()
