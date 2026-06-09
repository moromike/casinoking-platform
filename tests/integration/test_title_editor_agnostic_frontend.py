from __future__ import annotations

import re
from uuid import uuid4

import psycopg
import pytest
from psycopg.rows import dict_row
from playwright.sync_api import sync_playwright

from tests.integration.test_mines_embed_browser_smoke import _find_chromium_executable


def _seed_boxe_title(database_url: str) -> None:
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


def _cleanup_boxe_editor_state(database_url: str) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM boxe_admin_config WHERE title_code = 'boxe001'")


def _cleanup_boxe_title(database_url: str, title_code: str) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM boxe_admin_config WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
            cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


@pytest.mark.integration
def test_boxe_engine_page_inherits_variant_management_from_mines(
    frontend_base_url: str,
    wait_for_frontend,
    database_url: str,
    create_admin_user,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    _seed_boxe_title(database_url)
    title_code = f"boxe_browser_{uuid4().hex[:8]}"
    admin_user = create_admin_user(prefix="browser-boxe-engine-page")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=chromium_executable,
            )
            page = browser.new_page(viewport={"width": 1365, "height": 768})

            page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
            page.get_by_label("Email").fill(str(admin_user["email"]))
            page.get_by_label("Password").fill(str(admin_user["password"]))
            page.get_by_role("button", name="Sign in").click()
            page.get_by_role("button", name="Games").wait_for(timeout=10_000)

            page.goto(f"{frontend_base_url}/admin/games/boxe", wait_until="networkidle")
            page.locator("#games-category-boxe-title").wait_for(timeout=10_000)
            page.get_by_text("Editable titles").wait_for(timeout=10_000)
            page.get_by_role("button", name=re.compile(r"Active \(")).wait_for(timeout=10_000)
            page.get_by_text(re.compile(r"Test only \(")).wait_for(timeout=10_000)
            page.get_by_role("button", name="Create variant").wait_for(timeout=10_000)
            page.get_by_role("button", name="Preview").first.wait_for(timeout=10_000)
            page.get_by_role("button", name="Archive").first.wait_for(timeout=10_000)
            page.get_by_text("Demo on").first.wait_for(timeout=10_000)
            page.get_by_text("Real on").first.wait_for(timeout=10_000)

            page.get_by_label("Title code").first.fill(title_code)
            page.get_by_label("Display name").first.fill("BOXE Browser Variant")
            page.get_by_role("checkbox", name="Test", exact=True).check()

            with page.expect_response(
                lambda response: f"/api/v1/admin/games/titles/boxe/duplicate" in response.url
                and response.request.method == "POST"
                and response.status == 200
            ):
                page.get_by_role("button", name="Create variant").click()

            page.get_by_test_id("boxe-engine-editor").wait_for(timeout=10_000)
            assert f"/admin/games/boxe/titles/{title_code}" in page.url

            browser.close()
    finally:
        _cleanup_boxe_title(database_url, title_code)


@pytest.mark.integration
def test_boxe_title_editor_is_registered_and_saves_publishes_engine_config(
    api_base_url: str,
    frontend_base_url: str,
    wait_for_frontend,
    database_url: str,
    create_admin_user,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    _seed_boxe_title(database_url)
    _cleanup_boxe_editor_state(database_url)
    admin_user = create_admin_user(prefix="browser-title-editor-boxe")
    requests: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.on("request", lambda request: requests.append(request.url))

        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
        page.get_by_label("Email").fill(str(admin_user["email"]))
        page.get_by_label("Password").fill(str(admin_user["password"]))
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("button", name="Games").wait_for(timeout=10_000)

        page.goto(
            f"{frontend_base_url}/admin/games/boxe/titles/boxe001",
            wait_until="networkidle",
        )

        page.get_by_test_id("boxe-engine-editor").wait_for(timeout=10_000)
        page.get_by_text("BOXE overview").wait_for(timeout=10_000)
        page.get_by_text("BOXE diagnostics").wait_for(timeout=10_000)
        page.get_by_label("BOXE runtime language").wait_for(timeout=10_000)
        page.get_by_label("In-game title").wait_for(timeout=10_000)

        public_before_save = page.request.get(
            f"{api_base_url}/games/boxe/config?title_code=boxe001",
        )
        assert public_before_save.ok
        public_before_payload = public_before_save.json()["data"]
        assert public_before_payload["presentation_config"]["default_locale"] == "it"
        assert public_before_payload["presentation_config"]["copy"]["it"]["game.title"] == "BOXE"

        page.get_by_label("BOXE runtime language").select_option("en")
        page.get_by_label("In-game title").fill("BOXE Runtime English")
        page.get_by_role("button", name="Rows & difficulty").click()
        page.locator("label", has_text="5").get_by_role("checkbox").uncheck()
        with page.expect_response(
            lambda response: "/api/v1/admin/games/boxe/config/draft" in response.url
            and response.request.method == "PUT",
        ) as save_response_info:
            page.get_by_role("button", name="Save draft").click()
        assert save_response_info.value.ok
        page.get_by_text("Editor Status: Draft ready").wait_for(timeout=10_000)

        public_after_save = page.request.get(
            f"{api_base_url}/games/boxe/config?title_code=boxe001",
        )
        assert public_after_save.ok
        public_after_save_payload = public_after_save.json()["data"]
        assert public_after_save_payload["presentation_config"]["default_locale"] == "it"
        assert public_after_save_payload["presentation_config"]["copy"]["it"]["game.title"] == "BOXE"

        with page.expect_response(
            lambda response: "/api/v1/admin/games/boxe/config/publish" in response.url
            and response.request.method == "POST",
        ) as publish_response_info:
            page.get_by_role("button", name="Publish live").click()
        assert publish_response_info.value.ok
        page.get_by_text("Editor Status: Live").wait_for(timeout=10_000)

        public_after_publish = page.request.get(
            f"{api_base_url}/games/boxe/config?title_code=boxe001",
        )
        assert public_after_publish.ok
        public_after_publish_payload = public_after_publish.json()["data"]
        assert public_after_publish_payload["presentation_config"]["default_locale"] == "en"
        assert (
            public_after_publish_payload["presentation_config"]["copy"]["en"]["game.title"]
            == "BOXE Runtime English"
        )
        assert any(
            "/api/v1/games/boxe/config?title_code=boxe001" in request_url
            for request_url in requests
        )

        browser.close()

    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT rows_enabled_json, default_rows
                FROM boxe_admin_config
                WHERE title_code = 'boxe001'
                """
            )
            row = cursor.fetchone()
            assert row is not None
            assert row["rows_enabled_json"] == [4, 6, 7, 8]
            assert row["default_rows"] == 8

    _cleanup_boxe_editor_state(database_url)
