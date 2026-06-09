from __future__ import annotations

from pathlib import Path
import shutil
from urllib.parse import urlencode

import psycopg
from psycopg.rows import dict_row
import pytest


playwright = pytest.importorskip("playwright.sync_api")


def test_hi_lo_demo_boot_reaches_idle_gameplay(frontend_base_url: str, database_url: str) -> None:
    _seed_hi_lo_catalog(database_url)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        requests: list[str] = []
        config_statuses: list[int] = []
        page.on("request", lambda request: requests.append(request.url))
        page.on(
            "response",
            lambda response: config_statuses.append(response.status)
            if "/api/v1/games/hi-lo/config?title_code=hilo001" in response.url
            else None,
        )

        _open_hi_lo_gameplay(page, frontend_base_url)

        page.get_by_test_id("hi-lo-gameplay").wait_for()
        assert page.get_by_test_id("hi-lo-bet-button").is_enabled()
        assert any("/api/v1/games/hi-lo/config?title_code=hilo001" in url for url in requests)
        assert 200 in config_statuses
        browser.close()


def _open_hi_lo_gameplay(page, frontend_base_url: str) -> None:
    query = {
        "title_code": "hilo001",
        "mode": "demo",
    }
    page.goto(
        f"{frontend_base_url}/runtime/hi-lo?{urlencode(query)}",
        wait_until="networkidle",
    )
    page.locator(".game-provider-bootstrap-skip").click()
    page.get_by_role("button", name="Continua").click()
    page.get_by_test_id("hi-lo-gameplay").wait_for()


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


def _seed_hi_lo_catalog(database_url: str) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
                VALUES ('hi_lo', 'HI-LO', 'app.modules.games.hi_lo', 'active')
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
                    ('hi_lo', 'hi_lo', 'HI-LO Master', 'active', true, NULL),
                    ('hilo001', 'hi_lo', 'HI-LO 001', 'active', false, 'hi_lo')
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
                    ('casinoking', 'hi_lo', 920, 'active', 'hidden', false, false, 'HI-LO Master', 'Master HI-LO', false),
                    ('casinoking', 'hilo001', 921, 'active', 'visible', true, true, 'HI-LO', 'HI-LO test title', false)
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
            cursor.execute(
                """
                INSERT INTO title_configs (
                    title_code,
                    rules_sections_json,
                    ui_labels_json,
                    draft_rules_sections_json,
                    draft_ui_labels_json,
                    created_at,
                    updated_at
                )
                VALUES
                    ('hi_lo', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW()),
                    ('hilo001', '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, NOW(), NOW())
                ON CONFLICT (title_code) DO NOTHING
                """
            )
