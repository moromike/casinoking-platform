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
def test_mines_desktop_launcher_keeps_only_outer_close_action(
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
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.goto(frontend_base_url, wait_until="networkidle")
        page.get_by_role("link", name="Mines").click()
        page.wait_for_timeout(1000)

        action_buttons = page.locator(".mines-launch-header-actions button")
        action_button_labels = action_buttons.evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )
        heading_text = page.locator(".mines-launch-heading").inner_text()

        assert "Desktop launch stays embedded" not in heading_text
        assert action_button_labels == ["Fullscreen", "X"]
        assert page.get_by_role("button", name="Home").count() == 0

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
                const stage = document.querySelector('.mines-stage-card');
                const balance = document.querySelector('.mines-mobile-balance');
                const actions = document.querySelector('.mines-mobile-actions');
                const config = document.querySelector('.mines-mobile-config');
                const collectButton = Array.from(document.querySelectorAll('button')).find(
                    (button) => button.textContent?.trim() === 'Collect'
                );
                const doc = document.scrollingElement;
                const boardBox = board?.getBoundingClientRect() ?? null;
                const collectBox = collectButton?.getBoundingClientRect() ?? null;
                const previewWidths = Array.from(document.querySelectorAll('.mines-preview-chip')).map(
                    (node) => Math.round(node.getBoundingClientRect().width)
                );
                return {
                    innerHeight: window.innerHeight,
                    scrollHeight: doc ? doc.scrollHeight : -1,
                    boardTop: boardBox ? boardBox.top : null,
                    boardBottom: boardBox ? boardBox.bottom : null,
                    collectBottom: collectBox ? collectBox.bottom : null,
                    collectVisible: Boolean(
                        collectBox &&
                        collectBox.top >= 0 &&
                        collectBox.bottom <= window.innerHeight + 1
                    ),
                    subtitleText: document.querySelector('.mines-stage-subtitle')?.textContent?.trim() ?? '',
                    stageBottom: stage?.getBoundingClientRect().bottom ?? null,
                    balanceTop: balance?.getBoundingClientRect().top ?? null,
                    actionsTop: actions?.getBoundingClientRect().top ?? null,
                    configTop: config?.getBoundingClientRect().top ?? null,
                    previewWidths,
                };
            }
            """
        )

        assert metrics["scrollHeight"] <= metrics["innerHeight"] + 1
        assert metrics["boardTop"] is not None
        assert metrics["boardBottom"] is not None
        assert metrics["boardTop"] >= 0
        assert metrics["boardBottom"] <= metrics["innerHeight"] + 1
        assert metrics["collectVisible"] is True
        assert metrics["collectBottom"] is not None
        assert metrics["subtitleText"]
        assert metrics["stageBottom"] is not None
        assert metrics["balanceTop"] is not None
        assert metrics["actionsTop"] is not None
        assert metrics["configTop"] is not None
        if width <= height:
            assert metrics["stageBottom"] <= metrics["balanceTop"] + 1
            assert metrics["balanceTop"] <= metrics["actionsTop"] + 1
            assert metrics["actionsTop"] <= metrics["configTop"] + 1
        assert len(set(metrics["previewWidths"])) <= 1

        browser.close()


@pytest.mark.integration
def test_mines_embed_uses_compact_status_and_sliding_multiplier_window(
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
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.goto(f"{frontend_base_url}/mines?embed=1", wait_until="networkidle")
        page.get_by_role("button", name="5x5").click()
        page.locator(".field").nth(1).locator("button.choice-chip").filter(has_text="1").first.click()
        page.get_by_role("button", name="Bet").click()
        page.wait_for_timeout(1200)

        before = page.evaluate(
            """
            () => ({
                statusCount: document.querySelectorAll('.status-banner').length,
                rulesText: document.querySelector('.mines-rules-trigger')?.textContent?.trim(),
                demoBadge: document.querySelector('.mines-mode-badge')?.textContent?.trim(),
                innerHomeCount: Array.from(document.querySelectorAll('button')).filter(
                    (button) => button.textContent?.trim() === 'Home'
                ).length,
                stageCloseCount: document.querySelectorAll('.mines-stage-actions .mines-icon-close').length,
                preview: Array.from(document.querySelectorAll('.mines-preview-chip')).map(
                    (node) => node.textContent?.trim()
                ),
                activePreview: document.querySelector('.mines-preview-chip.active')?.textContent?.trim(),
            })
            """
        )

        after = None
        for _ in range(3):
            safe_reveal_recorded = False
            enabled_cells = page.locator(".board-cell:not(:disabled)")
            for index in range(enabled_cells.count()):
                enabled_cells.nth(index).click()
                page.wait_for_timeout(250)
                after = page.evaluate(
                    """
                    () => ({
                        preview: Array.from(document.querySelectorAll('.mines-preview-chip')).map(
                            (node) => node.textContent?.trim()
                        ),
                        activePreview: document.querySelector('.mines-preview-chip.active')?.textContent?.trim(),
                        previewCount: document.querySelectorAll('.mines-preview-chip').length,
                        subtitle: document.querySelector('.mines-stage-subtitle')?.textContent?.trim(),
                    })
                    """
                )
                if after["subtitle"] and after["subtitle"].startswith("Round "):
                    safe_reveal_recorded = True
                    break
                if after["subtitle"] and after["subtitle"].startswith("Hai perso"):
                    break

            if safe_reveal_recorded:
                break

            page.get_by_role("button", name="Bet").click()
            page.wait_for_timeout(350)
        assert after is not None

        assert before["statusCount"] == 0
        assert before["rulesText"] == "i"
        assert before["demoBadge"] == "DEMO MODE"
        assert before["innerHomeCount"] == 0
        assert before["stageCloseCount"] == 0
        assert len(before["preview"]) == 5
        assert len(after["preview"]) == 5
        assert after["subtitle"] is not None
        assert after["subtitle"].startswith("Round ")
        assert before["preview"][1:] == after["preview"][:4]
        assert after["activePreview"] == after["preview"][0]
        assert after["subtitle"].endswith(" live")

        browser.close()


@pytest.mark.integration
def test_mines_embed_limits_5x5_mine_choices_to_published_values(
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
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.goto(f"{frontend_base_url}/mines?embed=1", wait_until="networkidle")
        page.get_by_role("button", name="5x5").click()

        mine_values = page.locator(".field").filter(has_text="Mines").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )

        assert mine_values == ["1", "7", "13", "18", "24"]
        assert "25" not in mine_values

        browser.close()
