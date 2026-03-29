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
        "/snap/bin/chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


@pytest.mark.integration
def test_mines_embed_uses_selected_runtime_values_and_keeps_footer_visible(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1438, "height": 838})
        start_requests: list[dict[str, object]] = []

        def capture_request(request) -> None:
            if "/api/v1/games/mines/start" not in request.url:
                return
            payload = request.post_data or "{}"
            start_requests.append(json.loads(payload))

        page.on("request", capture_request)
        page.goto(f"{frontend_base_url}/mines?embed=1", wait_until="networkidle")

        mines_field = page.locator(".field").filter(has_text="Mines")
        bet_field = page.locator(".field").filter(has_text="Bet amount")

        page.get_by_role("button", name="6x6").click()
        mines_field.get_by_role("button", name="1", exact=True).click()
        bet_field.get_by_role("button", name="1", exact=True).click()
        page.get_by_role("button", name="Bet").click()

        page.wait_for_timeout(1200)

        assert start_requests, "Expected a POST /games/mines/start request."
        assert start_requests[-1] == {
            "grid_size": 36,
            "mine_count": 1,
            "bet_amount": "1",
            "wallet_type": "cash",
        }

        footer = page.locator(".mines-balance-footer")
        assert footer.is_visible()
        footer_text = footer.inner_text()
        assert "balance" in footer_text.lower()
        assert "win" in footer_text.lower()

        browser.close()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("width", "height"),
    [
        (375, 667),
        (882, 344),
    ],
)
def test_mines_mobile_surface_stays_inside_viewport_on_short_screens(
    frontend_base_url: str,
    wait_for_frontend,
    width: int,
    height: int,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{frontend_base_url}/mines", wait_until="networkidle")

        metrics = page.evaluate(
            """
            () => {
                const board = document.querySelector('.mines-board');
                const doc = document.scrollingElement;
                const boardBox = board?.getBoundingClientRect() ?? null;
                return {
                    innerHeight: window.innerHeight,
                    scrollHeight: doc ? doc.scrollHeight : -1,
                    boardTop: boardBox ? boardBox.top : null,
                    boardBottom: boardBox ? boardBox.bottom : null,
                };
            }
            """
        )

        assert metrics["scrollHeight"] <= metrics["innerHeight"] + 1
        assert metrics["boardTop"] is not None
        assert metrics["boardBottom"] is not None
        assert metrics["boardTop"] >= 0
        assert metrics["boardBottom"] <= metrics["innerHeight"] + 1

        browser.close()
