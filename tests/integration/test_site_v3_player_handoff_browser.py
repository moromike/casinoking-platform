from __future__ import annotations

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
        shutil.which("msedge"),
        "/snap/bin/chromium",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


@pytest.mark.integration
def test_site_v3_login_account_handoff_returns_to_public_site(
    public_edge_base_url: str,
    wait_for_public_edge,
    create_player,
) -> None:
    del wait_for_public_edge

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser handoff smoke test.")

    player = create_player(prefix="site-v3-handoff")
    public_root = public_edge_base_url.rstrip("/")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        page.goto(f"{public_root}/", wait_until="networkidle")
        login_href = page.locator("a.is-login").get_attribute("href")
        assert login_href is not None
        assert login_href.startswith("/login?return_to=")

        page.locator("a.is-login").click()
        page.wait_for_url("**/login?return_to=**", wait_until="networkidle")
        page.locator("form").get_by_label("Email", exact=True).fill(str(player["email"]))
        page.locator("form").get_by_label("Password", exact=True).fill(str(player["password"]))
        page.locator("form").get_by_role("button", name="Sign in", exact=True).click()

        page.wait_for_url(f"{public_root}/", wait_until="networkidle", timeout=15000)
        page.wait_for_function(
            """
            () => {
                const token = window.localStorage.getItem('casinoking.access_token');
                return Boolean(token)
                    && document.querySelector('a.is-account')
                    && !document.querySelector('a.is-login');
            }
            """,
            timeout=15000,
        )

        account_href = page.locator("a.is-account").get_attribute("href")
        assert account_href is not None
        assert account_href.startswith("/account?return_to=")

        page.locator("a.is-account").click()
        page.wait_for_url("**/account?return_to=**", wait_until="networkidle")
        page.get_by_role("button", name="Esci", exact=True).click()

        page.wait_for_url(f"{public_root}/", wait_until="networkidle", timeout=15000)
        page.wait_for_function(
            """
            () => {
                const token = window.localStorage.getItem('casinoking.access_token');
                return !token
                    && document.querySelector('a.is-login')
                    && document.querySelector('a.is-account');
            }
            """,
            timeout=15000,
        )
        browser.close()


@pytest.mark.integration
def test_site_v3_game_launch_links_preserve_return_to(
    public_edge_base_url: str,
    wait_for_public_edge,
) -> None:
    del wait_for_public_edge

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser handoff smoke test.")

    public_root = public_edge_base_url.rstrip("/")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1366, "height": 900})

        page.goto(f"{public_root}/", wait_until="networkidle")
        cards = page.locator("button.site-v3-game-card")
        assert cards.count() > 0
        cards.nth(0).click()

        launch_links = page.locator("a.site-v3-launch-option")
        assert launch_links.count() > 0
        hrefs = [
            launch_links.nth(index).get_attribute("href")
            for index in range(launch_links.count())
        ]
        assert all(href is not None and "return_to=" in href for href in hrefs)
        assert all(str(href).startswith(f"{public_root}/") for href in hrefs)

        launch_href = str(next(href for href in hrefs if href is not None))
        page.goto(launch_href, wait_until="networkidle")
        page.locator(".site-v3-game-host").wait_for(timeout=15_000)
        frame_src = page.locator("iframe.site-v3-game-frame").get_attribute("src")
        assert frame_src is not None
        assert frame_src.startswith("/legacy-games/")
        assert "embed=1" in frame_src
        assert "embed_origin=" in frame_src
        assert "return_to=" in frame_src
        frame_text = page.frame_locator("iframe.site-v3-game-frame").locator("body").text_content(timeout=15_000) or ""
        assert any(label in frame_text for label in ["Mines", "BOXE", "HI-LO"])
        browser.close()
