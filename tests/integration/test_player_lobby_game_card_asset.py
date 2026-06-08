from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from tests.integration.test_site_v3_backend import _cleanup_site_v3_page

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


def _png_bytes() -> bytes:
    """Minimal valid 1x1 PNG."""
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00,
        0x01, 0x01, 0x00, 0x05, 0x18, 0xD8, 0xB4, 0x78,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82,
    ])


def _modules_for_lobby_card(*, title_code: str, cta_label: str = "Play demo") -> list[dict[str, object]]:
    return [
        {
            "module_code": "global_header",
            "slot_key": "header",
            "sort_order": 0,
            "config_json": {"brand_label": "CasinoKing"},
        },
        {
            "module_code": "hero_banner",
            "slot_key": "hero",
            "sort_order": 0,
            "config_json": {
                "headline": "Play now",
                "body": "A published hero",
                "cta_label": cta_label,
                "cta_title_code": title_code,
            },
        },
        {
            "module_code": "game_grid",
            "slot_key": "games",
            "sort_order": 0,
            "config_json": {
                "heading": "Games",
                "title_codes": [title_code],
            },
        },
        {
            "module_code": "global_footer",
            "slot_key": "footer",
            "sort_order": 0,
            "config_json": {"legal_text": "18+ Play responsibly."},
        },
    ]


def _create_and_publish_site_v3_page(
    *,
    client,
    headers: dict[str, str],
    page_code: str,
    title_code: str,
    cta_label: str = "Play demo",
) -> None:
    draft_response = client.put(
        f"/admin/site-v3/sites/casinoking/pages/{page_code}/draft",
        headers=headers,
        json={
            "locale": "it",
            "title": "Lobby Card Test",
            "modules": _modules_for_lobby_card(title_code=title_code, cta_label=cta_label),
        },
    )
    assert draft_response.status_code == 200, draft_response.text

    publish_response = client.post(
        f"/admin/site-v3/sites/casinoking/pages/{page_code}/publish",
        headers=headers,
        json={"locale": "it", "expected_draft_version": 1},
    )
    assert publish_response.status_code == 200, publish_response.text


def _setup_lobby_test(
    *,
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
    cta_label: str = "Play demo",
):
    admin = create_admin_user(prefix="lobby-card-admin")
    headers = auth_headers(admin["access_token"], include_game_launch_token=False)
    page_code = f"lobby-card-{uuid4().hex[:8]}"
    title = create_published_mines_variant(
        title_code=f"mines_lobby_{uuid4().hex[:8]}",
        display_name="Mines Card Test",
        demo_enabled=True,
        real_enabled=True,
    )
    title_code = str(title["title_code"])

    # Upload game_card asset
    asset_response = client.post(
        f"/admin/titles/{title_code}/assets",
        headers=headers,
        data={"asset_kind": "game_card"},
        files={"file": ("card.png", _png_bytes(), "image/png")},
    )
    assert asset_response.status_code == 200, asset_response.text
    public_url = asset_response.json()["data"]["public_url"]

    # Create and publish Site V3 page
    _create_and_publish_site_v3_page(
        client=client,
        headers=headers,
        page_code=page_code,
        title_code=title_code,
        cta_label=cta_label,
    )

    return {
        "admin": admin,
        "headers": headers,
        "page_code": page_code,
        "title": title,
        "title_code": title_code,
        "public_url": public_url,
    }


def _teardown_lobby_test(*, client, setup_result, db_connection):
    title_code = setup_result["title_code"]
    page_code = setup_result["page_code"]
    headers = setup_result["headers"]

    client.delete(
        f"/admin/titles/{title_code}/assets/game_card",
        headers=headers,
    )
    _cleanup_site_v3_page(db_connection=db_connection, page_code=page_code)


@pytest.mark.integration
def test_player_lobby_renders_game_card_asset_and_opens_launch_cashier(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
    site_v3_frontend_base_url: str,
    wait_for_site_v3_frontend,
) -> None:
    del wait_for_site_v3_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    setup = _setup_lobby_test(
        client=client,
        create_admin_user=create_admin_user,
        auth_headers=auth_headers,
        create_published_mines_variant=create_published_mines_variant,
        db_connection=db_connection,
    )

    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=chromium_executable,
            )
            page = browser.new_page(viewport={"width": 1015, "height": 768})
            page.goto(f"{site_v3_frontend_base_url}/pages/{setup['page_code']}", wait_until="networkidle")

            # Wait for game card button
            card_button = page.get_by_role("button", name=f"Open launch cashier for {setup['title']['display_name']}")
            card_button.wait_for()

            # Verify artwork image is rendered with uploaded asset
            art_img = page.locator("img.site-v3-game-art").first
            art_img.wait_for()
            src = art_img.get_attribute("src")
            assert setup["public_url"] in src

            # The game card itself is a button; it contains no direct demo/login links
            card = page.locator(".site-v3-game-card").first
            assert card.get_by_role("link").count() == 0

            # Open launch cashier
            card_button.click()
            page.get_by_role("dialog", name=setup["title"]["display_name"]).wait_for()
            assert page.get_by_text("Launch cashier").is_visible()

            # Verify disabled reasons for unauthenticated player
            assert page.get_by_text("Log in before using real balance.").is_visible()
            assert page.get_by_text("Log in before using bonus balance.").is_visible()
            assert page.locator(".player-lobby-cashier-option").nth(0).is_disabled()
            assert page.locator(".player-lobby-cashier-option").nth(1).is_disabled()

            # Click demo option → navigates to game
            page.locator(".player-lobby-cashier-option").nth(2).click()
            page.wait_for_url("**/mines?*")
            assert f"title_code={setup['title_code']}" in page.url
            assert "mode=demo" in page.url

            browser.close()
    finally:
        _teardown_lobby_test(client=client, setup_result=setup, db_connection=db_connection)


@pytest.mark.integration
def test_player_lobby_home_slot_cta_navigates_to_game(
    client,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_connection,
    site_v3_frontend_base_url: str,
    wait_for_site_v3_frontend,
) -> None:
    del wait_for_site_v3_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    setup = _setup_lobby_test(
        client=client,
        create_admin_user=create_admin_user,
        auth_headers=auth_headers,
        create_published_mines_variant=create_published_mines_variant,
        db_connection=db_connection,
        cta_label="Play now",
    )

    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=chromium_executable,
            )
            page = browser.new_page(viewport={"width": 1015, "height": 768})
            page.goto(f"{site_v3_frontend_base_url}/pages/{setup['page_code']}", wait_until="networkidle")

            # HeroBanner CTA is an <a>, not a <button>
            cta_link = page.locator("a.site-v3-primary-link").filter(has_text="Play now")
            cta_link.wait_for()

            href = cta_link.get_attribute("href")
            assert setup["title_code"] in href
            # resolveCtaHref defaults to demo when mode is unspecified
            assert "mode=demo" in href

            # Click navigates to the game route
            cta_link.click()
            page.wait_for_url("**/mines?*")
            assert f"title_code={setup['title_code']}" in page.url
            assert "mode=demo" in page.url

            browser.close()
    finally:
        _teardown_lobby_test(client=client, setup_result=setup, db_connection=db_connection)
