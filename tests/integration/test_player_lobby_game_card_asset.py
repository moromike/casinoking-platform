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


def _library_payload() -> dict[str, object]:
    return {
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


def _runtime_config_payload() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "game_code": "mines",
            "supported_grid_sizes": [25],
            "supported_mine_counts": {"25": [3]},
            "payout_ladders": {"25": {"3": ["1.1"]}},
            "fairness_version": "test",
            "presentation_config": {
                "rules_sections": {},
                "published_grid_sizes": [25],
                "published_mine_counts": {"25": [3]},
                "default_mine_counts": {"25": 3},
                "ui_labels": {},
                "i18n": {
                    "published_locale": "en",
                    "resolved_locale": "en",
                    "default_locale": "en",
                    "fallback_locale": "en",
                    "copy": {},
                },
            },
        },
    }


def _route_lobby_api(page, *, home_payload: dict[str, object]) -> None:
    page.route(
        "**/api/v1/games/library*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_library_payload()),
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
    page.route(
        "**/api/v1/games/mines/config*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_runtime_config_payload()),
        ),
    )


@pytest.mark.integration
def test_player_lobby_renders_game_card_asset_and_opens_launch_cashier(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

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
        _route_lobby_api(page, home_payload=home_payload)

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
        assert page.get_by_role("link", name="Demo").count() == 0
        assert page.get_by_role("link", name="Log in to play").count() == 0

        page.get_by_role("button", name="Open launch cashier for Mines Card Test").click()
        page.get_by_role("dialog", name="Mines Card Test").wait_for()
        assert page.get_by_text("Launch cashier").is_visible()
        assert page.get_by_text("Log in to use real balance.").is_visible()
        assert page.get_by_text("Log in to use bonus balance.").is_visible()
        assert page.locator(".player-lobby-cashier-option").nth(0).is_disabled()
        assert page.locator(".player-lobby-cashier-option").nth(1).is_disabled()

        page.locator(".player-lobby-cashier-option").nth(2).click()
        page.wait_for_url("**/mines?*")
        assert "title_code=mines_card_test" in page.url
        assert "mode=demo" in page.url

        browser.close()


@pytest.mark.integration
def test_player_lobby_home_slot_cta_opens_launch_cashier(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    home_payload = {
        "success": True,
        "data": {
            "site": {
                "site_code": "casinoking",
                "display_name": "CasinoKing",
                "status": "active",
            },
            "slots": [
                {
                    "id": "slot-1",
                    "site_code": "casinoking",
                    "slot_key": "hero",
                    "title": "Mines hero",
                    "subtitle": "Open the cashier.",
                    "cta_label": "Play now",
                    "cta_target_type": "title_real",
                    "cta_target_ref": "mines_card_test",
                    "media_asset_id": None,
                    "media_asset": None,
                    "sort_order": 1,
                }
            ],
        },
    }

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1015, "height": 768})
        _route_lobby_api(page, home_payload=home_payload)

        page.goto(frontend_base_url, wait_until="networkidle")
        page.get_by_role("button", name="Play now").click()
        page.get_by_role("dialog", name="Mines Card Test").wait_for()
        assert page.get_by_text("Launch cashier").is_visible()

        browser.close()
