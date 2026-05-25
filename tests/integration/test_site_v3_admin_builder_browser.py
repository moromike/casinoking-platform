from uuid import uuid4

import pytest
from playwright.sync_api import sync_playwright

from tests.integration.test_mines_embed_browser_smoke import _find_chromium_executable


@pytest.mark.integration
def test_site_v3_admin_builder_draft_validate_publish_smoke(
    frontend_base_url: str,
    wait_for_frontend,
    create_admin_user,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="site-v3-admin-builder")
    page_code = f"smoke-{uuid4().hex[:8]}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        try:
            page = browser.new_page(viewport={"width": 1365, "height": 768})

            page.goto(f"{frontend_base_url}/admin/site-v3", wait_until="domcontentloaded")
            page.get_by_label("Email").fill(str(admin_user["email"]))
            page.get_by_label("Password").fill(str(admin_user["password"]))
            page.get_by_role("button", name="Sign in").click()

            page.locator("[data-testid='site-v3-admin-builder']").wait_for(timeout=30_000)
            page.get_by_role("button", name="New page").click()
            page.get_by_label("Page code").fill(page_code)
            page.get_by_label("Title").fill("Smoke Site V3 page")

            page.get_by_label("Add module").select_option("hero_banner")
            hero_card = page.locator(".site-v3-module-card").filter(has_text="Hero banner")
            hero_card.wait_for(timeout=10_000)
            page.get_by_role("button", name="Validate").click()
            page.get_by_text("headline is required").wait_for(timeout=10_000)

            hero_card.get_by_label("Headline").fill("Smoke hero")
            page.get_by_role("button", name="Save draft").click()
            page.get_by_text("Draft saved").wait_for(timeout=15_000)

            page.get_by_role("button", name="Validate").click()
            page.get_by_text("Validation green", exact=True).wait_for(timeout=10_000)
            page.get_by_role("button", name="Publish live").click()
            page.get_by_text("Published version").wait_for(timeout=15_000)
            page.get_by_text("History").wait_for(timeout=10_000)
        finally:
            browser.close()
