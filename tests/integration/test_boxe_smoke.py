from __future__ import annotations

from pathlib import Path
import shutil

import psycopg
from psycopg.rows import dict_row
import pytest


playwright = pytest.importorskip("playwright.sync_api")


def test_boxe_demo_boot_reaches_placeholder(frontend_base_url: str, database_url: str) -> None:
    _seed_boxe_catalog(database_url)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        requests: list[str] = []
        page.on("request", lambda request: requests.append(request.url))

        page.goto(
            f"{frontend_base_url}/boxe?title_code=boxe001&mode=demo",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="Entra").click()
        page.get_by_role("button", name="Continua").click()
        page.get_by_test_id("boxe-table-balance-gate").get_by_role(
            "button",
            name="Continua",
        ).click()

        page.get_by_role("heading", name="BOXE gameplay - 3B in arrivo").wait_for()
        assert page.get_by_text("98% RTP").is_visible()
        assert any("/api/v1/games/boxe/config?title_code=boxe001" in url for url in requests)
        browser.close()


def test_boxe_short_landscape_rotation_gate(frontend_base_url: str, database_url: str) -> None:
    _seed_boxe_catalog(database_url)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 882, "height": 344})
        page.goto(
            f"{frontend_base_url}/boxe?title_code=boxe001&mode=demo",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="Entra").click()
        page.get_by_role("button", name="Continua").click()
        page.get_by_test_id("boxe-table-balance-gate").get_by_role(
            "button",
            name="Continua",
        ).click()

        page.get_by_role("status", name="Ruota il dispositivo").wait_for()
        assert page.get_by_text("BOXE gameplay - 3B in arrivo").is_visible()
        browser.close()


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


def _seed_boxe_catalog(database_url: str) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
                VALUES ('boxe', 'BOXE', 'app.modules.games.boxe', 'active')
                ON CONFLICT (engine_code) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    runtime_module = EXCLUDED.runtime_module,
                    status = 'active'
                """
            )
            cursor.execute(
                """
                INSERT INTO game_titles (
                    title_code,
                    engine_code,
                    display_name,
                    status,
                    is_master,
                    source_title_code
                )
                VALUES
                    ('boxe', 'boxe', 'BOXE Master', 'active', true, NULL),
                    ('boxe001', 'boxe', 'BOXE 001', 'active', false, 'boxe')
                ON CONFLICT (title_code) DO UPDATE
                SET engine_code = EXCLUDED.engine_code,
                    display_name = EXCLUDED.display_name,
                    status = 'active',
                    is_master = EXCLUDED.is_master,
                    source_title_code = EXCLUDED.source_title_code,
                    updated_at = NOW()
                """
            )
            cursor.execute(
                """
                INSERT INTO site_titles (
                    site_code,
                    title_code,
                    position,
                    status,
                    lobby_visibility,
                    demo_enabled,
                    real_enabled,
                    lobby_display_name,
                    lobby_description,
                    featured
                )
                VALUES
                    ('casinoking', 'boxe', 900, 'active', 'hidden', false, false, 'BOXE Master', 'Master BOXE', false),
                    ('casinoking', 'boxe001', 901, 'active', 'visible', true, true, 'BOXE', 'BOXE test title', false)
                ON CONFLICT (site_code, title_code) DO UPDATE
                SET status = 'active',
                    lobby_visibility = EXCLUDED.lobby_visibility,
                    demo_enabled = EXCLUDED.demo_enabled,
                    real_enabled = EXCLUDED.real_enabled,
                    lobby_display_name = EXCLUDED.lobby_display_name,
                    lobby_description = EXCLUDED.lobby_description,
                    featured = EXCLUDED.featured,
                    updated_at = NOW()
                """
            )
