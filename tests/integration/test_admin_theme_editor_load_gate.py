import json

import pytest
from playwright.sync_api import sync_playwright

from tests.integration.test_mines_embed_browser_smoke import (
    _browser_duplicate_mines_variant,
    _find_chromium_executable,
)


@pytest.mark.integration
def test_admin_theme_editor_hides_fallback_controls_until_theme_loads(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    auth_headers,
    track_mines_variant_cleanup,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="browser-admin-theme-load-gate")
    title_code = track_mines_variant_cleanup(
        _browser_duplicate_mines_variant(
            client,
            auth_headers,
            admin_user=admin_user,
        )
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        held_theme_route = {}

        def hold_theme(route) -> None:
            held_theme_route["route"] = route

        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
        page.get_by_label("Email").fill(str(admin_user["email"]))
        page.get_by_label("Password").fill(str(admin_user["password"]))
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("button", name="Games").wait_for()

        page.route(f"**/api/v1/admin/titles/{title_code}/theme", hold_theme)
        page.goto(
            f"{frontend_base_url}/admin/games/mines/titles/{title_code}",
            wait_until="domcontentloaded",
        )
        page.get_by_role("button", name="Theme").wait_for(timeout=10_000)
        page.get_by_role("button", name="Theme").click()

        page.get_by_text("Theme not loaded").wait_for(timeout=10_000)
        page.get_by_text("Load the theme to open the editor.").wait_for(timeout=10_000)
        assert page.locator(".theme-editor-section").count() == 0
        assert page.locator(".skin-asset-row").count() == 0
        assert (
            page.locator(".theme-editor-actions").get_by_role("button", name="Save draft").count()
            == 0
        )
        assert (
            page.locator(".theme-editor-actions")
            .get_by_role("button", name="Publish live")
            .count()
            == 0
        )

        for _ in range(50):
            if held_theme_route:
                break
            page.wait_for_timeout(100)
        assert held_theme_route
        held_theme_route["route"].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "title_code": title_code,
                        "published": {
                            "tokens": {
                                "--ck-bg": "#09090f",
                                "--ck-surface": "#181924",
                                "--ck-accent": "#56dc49",
                            },
                            "skin": None,
                        },
                        "draft": {
                            "tokens": {
                                "--ck-bg": "#09090f",
                                "--ck-surface": "#181924",
                                "--ck-accent": "#56dc49",
                            },
                            "skin": None,
                        },
                        "has_unpublished_changes": False,
                        "draft_updated_at": None,
                        "published_at": None,
                    },
                }
            ),
        )

        page.get_by_text("Preset skin").wait_for(timeout=10_000)
        assert page.locator(".theme-editor-section").count() > 0
        assert (
            page.locator(".theme-editor-actions").get_by_role("button", name="Reload theme").count()
            == 1
        )

        browser.close()
