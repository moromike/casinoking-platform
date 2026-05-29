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
        assert login_href.startswith(f"{public_root}/login?return_to=")

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
        assert account_href.startswith(f"{public_root}/account?return_to=")

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
