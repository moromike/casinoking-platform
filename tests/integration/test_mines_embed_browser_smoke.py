from __future__ import annotations

import json
from pathlib import Path
import shutil
from urllib.request import urlopen

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


def _load_public_mines_config() -> dict[str, object]:
    with urlopen("http://localhost:8000/api/v1/games/mines/config") as response:
        return json.loads(response.read().decode("utf-8"))["data"]


def _publish_browser_mines_config(
    client,
    create_admin_user,
    auth_headers,
    *,
    published_grid_sizes: list[int],
    published_mine_counts: dict[str, list[int]],
    default_mine_counts: dict[str, int],
) -> None:
    admin_user = create_admin_user(prefix="browser-mines-admin")
    payload = {
        "rules_sections": {
            "ways_to_win": "<p>Pick at least one diamond, then collect.</p>",
            "payout_display": "<p>The highlighted multiplier is the payout available right now.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Authenticated players can inspect completed hands from account history.</p>",
        },
        "published_grid_sizes": published_grid_sizes,
        "published_mine_counts": published_mine_counts,
        "default_mine_counts": default_mine_counts,
        "ui_labels": {
            "demo": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
            "real": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }
    draft_response = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(admin_user["access_token"]),
        json=payload,
    )
    assert draft_response.status_code == 200
    publish_response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200


@pytest.mark.integration
def test_mines_embed_uses_selected_runtime_values_and_keeps_footer_visible(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    auth_headers,
) -> None:
    del wait_for_frontend
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[25, 36],
        published_mine_counts={"25": [1, 7, 13, 18, 24], "36": [1, 9, 18, 27, 35]},
        default_mine_counts={"25": 13, "36": 18},
    )

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

        grid_labels = page.locator(".field").filter(has_text="Grid size").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim()).filter(Boolean)"
        )
        target_grid_label = grid_labels[-1]
        target_grid_size = int(target_grid_label.split("x")[0]) ** 2

        page.get_by_role("button", name=target_grid_label).click()
        mines_field.get_by_role("button", name="1", exact=True).click()
        bet_field.get_by_role("button", name="1", exact=True).click()
        page.get_by_role("button", name="Bet").click()
        page.wait_for_function(
            """
            () => {
                const interactiveCells = document.querySelectorAll('.board-cell:not(:disabled)').length;
                const disabledGridChip = document.querySelector('.field:nth-of-type(1) button.choice-chip:disabled');
                return interactiveCells > 0 && Boolean(disabledGridChip);
            }
            """
        )

        page.wait_for_timeout(1200)

        assert start_requests, "Expected a POST /games/mines/start request."
        assert start_requests[-1] == {
            "grid_size": target_grid_size,
            "mine_count": 1,
            "bet_amount": "1",
            "wallet_type": "cash",
        }

        active_controls = page.evaluate(
            """
            () => ({
                activeGrid: document.querySelector('.field:nth-of-type(1) .choice-chip.active')?.textContent?.trim() ?? '',
                activeMines: document.querySelector('.field:nth-of-type(2) .choice-chip.active')?.textContent?.trim() ?? '',
                gridDisabled: Boolean(document.querySelector('.field:nth-of-type(1) button.choice-chip:disabled')),
                minesDisabled: Boolean(document.querySelector('.field:nth-of-type(2) button.choice-chip:disabled')),
            })
            """
        )
        assert active_controls["activeGrid"] == target_grid_label
        assert active_controls["activeMines"] == "1"
        assert active_controls["gridDisabled"] is True
        assert active_controls["minesDisabled"] is True

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
def test_mines_embed_desktop_controls_do_not_overlap_actions(
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
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.goto(f"{frontend_base_url}/mines?embed=1", wait_until="networkidle")
        grid_labels = page.locator(".field").filter(has_text="Grid size").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim()).filter(Boolean)"
        )
        page.get_by_role("button", name=grid_labels[-1]).click()
        mine_labels = page.locator(".field").filter(has_text="Mines").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim()).filter(Boolean)"
        )
        page.locator(".field").filter(has_text="Mines").get_by_role(
            "button",
            name=mine_labels[min(len(mine_labels) - 1, 1)],
            exact=True,
        ).click()
        page.get_by_role("button", name="Bet").click()
        page.wait_for_function(
            """
            () => {
                const interactiveCells = document.querySelectorAll('.board-cell:not(:disabled)').length;
                const disabledGridChip = document.querySelector('.field:nth-of-type(1) button.choice-chip:disabled');
                return interactiveCells > 0 && Boolean(disabledGridChip);
            }
            """
        )
        metrics = page.evaluate(
            """
            () => {
                const betField = document.querySelector('#bet-amount-standalone')?.closest('.field');
                const quick = betField?.querySelector('.quick-chip-row');
                const actions = document.querySelector('.mines-control-rail .actions');
                const rect = (node) => node ? node.getBoundingClientRect() : null;
                return {
                    quickBottom: rect(quick)?.bottom ?? null,
                    actionsTop: rect(actions)?.top ?? null,
                };
            }
            """
        )
        assert metrics["quickBottom"] is not None
        assert metrics["actionsTop"] is not None
        assert metrics["quickBottom"] <= metrics["actionsTop"]
        browser.close()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("route", "width", "height"),
    [
        ("/mines", 375, 667),
        ("/mines", 882, 344),
        ("/mines?embed=1", 375, 667),
        ("/mines?embed=1", 882, 344),
    ],
)
def test_mines_mobile_surface_stays_inside_viewport_on_short_screens(
    frontend_base_url: str,
    wait_for_frontend,
    route: str,
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
        page.goto(f"{frontend_base_url}{route}", wait_until="networkidle")

        metrics = page.evaluate(
            """
            () => {
                const board = document.querySelector('.mines-board');
                const stage = document.querySelector('.mines-stage-card');
                const playStack = document.querySelector('.mines-mobile-play-stack');
                const settingsSummary = document.querySelector('.mines-mobile-settings-summary .mines-mobile-settings-chip');
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
                    stageBottom: stage?.getBoundingClientRect().bottom ?? null,
                    playTop: playStack?.getBoundingClientRect().top ?? null,
                    settingsSummaryVisible: Boolean(
                        settingsSummary &&
                        settingsSummary.getBoundingClientRect().top >= 0 &&
                        settingsSummary.getBoundingClientRect().bottom <= window.innerHeight + 1
                    ),
                    previewWidths,
                    boardExists: Boolean(board),
                };
            }
            """
        )

        assert metrics["boardExists"] is True
        assert metrics["scrollHeight"] <= metrics["innerHeight"] + 1
        assert metrics["boardTop"] is not None
        assert metrics["boardBottom"] is not None
        assert metrics["boardTop"] >= 0
        assert metrics["boardBottom"] <= metrics["innerHeight"] + 1
        minimum_board_size = 220 if width <= height else 160
        assert metrics["boardBottom"] - metrics["boardTop"] >= minimum_board_size
        assert metrics["collectVisible"] is True
        assert metrics["collectBottom"] is not None
        assert metrics["stageBottom"] is not None
        assert metrics["playTop"] is not None
        assert metrics["settingsSummaryVisible"] is True
        if width <= height:
            assert metrics["stageBottom"] <= metrics["playTop"] + 1
        assert len(set(metrics["previewWidths"])) <= 1

        page.locator(".mines-mobile-settings-summary .mines-mobile-settings-chip").first.click()
        page.wait_for_function("() => document.querySelector('.mines-mobile-settings-sheet') !== null")
        sheet_metrics = page.evaluate(
            """
            () => {
                const sheet = document.querySelector('.mines-mobile-settings-sheet');
                const gridButtons = sheet?.querySelectorAll('.field:nth-of-type(1) .choice-chip').length ?? 0;
                const mineButtons = sheet?.querySelectorAll('.field:nth-of-type(2) .choice-chip').length ?? 0;
                const sheetBox = sheet?.getBoundingClientRect() ?? null;
                return {
                    gridButtons,
                    mineButtons,
                    sheetBottom: sheetBox ? sheetBox.bottom : null,
                };
            }
            """
        )
        assert sheet_metrics["gridButtons"] > 0
        assert sheet_metrics["mineButtons"] > 0
        assert sheet_metrics["sheetBottom"] is not None
        assert sheet_metrics["sheetBottom"] <= height + 1

        browser.close()


@pytest.mark.integration
def test_mines_embed_uses_compact_status_and_sliding_multiplier_window(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    auth_headers,
) -> None:
    del wait_for_frontend
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[25],
        published_mine_counts={"25": [1]},
        default_mine_counts={"25": 1},
    )

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

        grid_labels = page.locator(".field").filter(has_text="Grid size").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim()).filter(Boolean)"
        )
        target_grid_label = grid_labels[0]
        page.get_by_role("button", name=target_grid_label).click()
        page.locator(".field").nth(1).locator("button.choice-chip").first.click()
        page.get_by_role("button", name="Bet").click()
        page.wait_for_function("() => document.querySelectorAll('.board-cell:not(:disabled)').length > 0")
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
def test_mines_embed_renders_real_board_symbols_in_dom(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        published_grid_sizes=[25],
        published_mine_counts={"25": [1]},
        default_mine_counts={"25": 1},
    )

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
        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url and response.request.method == "POST"
        ) as start_response_info:
            page.get_by_role("button", name="Bet").click()
        session_id = start_response_info.value.json()["data"]["game_session_id"]
        assert session_id
        access_token = page.evaluate(
            "() => window.localStorage.getItem('casinoking.access_token') || ''"
        )
        assert access_token
        page.wait_for_timeout(800)
        mine_positions = set(db_helpers.get_mine_positions(session_id))
        safe_cell = next(index for index in range(25) if index not in mine_positions)
        mine_cell = next(iter(mine_positions))

        page.locator(".board-cell").nth(safe_cell).click()
        page.wait_for_function(
            """
            () =>
                document.querySelectorAll(
                    '.board-cell.revealed-safe .board-cell-face-visual svg, .board-cell.revealed-safe .board-cell-face-visual img'
                ).length > 0
            """
        )
        page.wait_for_timeout(250)
        safe_metrics = page.evaluate(
            """
            () => ({
                safeSymbols: document.querySelectorAll('.board-cell.revealed-safe .board-cell-face-visual svg, .board-cell.revealed-safe .board-cell-face-visual img').length,
                safeCentered: (() => {
                    const cell = document.querySelector('.board-cell.revealed-safe');
                    const symbol = document.querySelector('.board-cell.revealed-safe .board-cell-face-visual svg, .board-cell.revealed-safe .board-cell-face-visual img');
                    if (!cell || !symbol) {
                        return null;
                    }
                    const cellBox = cell.getBoundingClientRect();
                    const symbolBox = symbol.getBoundingClientRect();
                    const cellCenterX = cellBox.left + cellBox.width / 2;
                    const cellCenterY = cellBox.top + cellBox.height / 2;
                    const symbolCenterX = symbolBox.left + symbolBox.width / 2;
                    const symbolCenterY = symbolBox.top + symbolBox.height / 2;
                    return {
                        xDelta: Math.abs(cellCenterX - symbolCenterX),
                        yDelta: Math.abs(cellCenterY - symbolCenterY),
                    };
                })(),
            })
            """
        )
        assert safe_metrics["safeSymbols"] > 0
        assert safe_metrics["safeCentered"] is not None
        assert safe_metrics["safeCentered"]["xDelta"] <= 6
        assert safe_metrics["safeCentered"]["yDelta"] <= 6

        page.locator(".board-cell").nth(mine_cell).click()
        page.wait_for_function(
            """
            () =>
                document.querySelectorAll(
                    '.board-cell.revealed-mine .board-cell-face-visual svg, .board-cell.revealed-mine .board-cell-face-visual img'
                ).length > 0
            """
        )
        page.wait_for_timeout(250)
        mine_metrics = page.evaluate(
            """
            () => ({
                mineSymbols: document.querySelectorAll('.board-cell.revealed-mine .board-cell-face-visual svg, .board-cell.revealed-mine .board-cell-face-visual img').length,
                mineCentered: (() => {
                    const cell = document.querySelector('.board-cell.revealed-mine');
                    const symbol = document.querySelector('.board-cell.revealed-mine .board-cell-face-visual svg, .board-cell.revealed-mine .board-cell-face-visual img');
                    if (!cell || !symbol) {
                        return null;
                    }
                    const cellBox = cell.getBoundingClientRect();
                    const symbolBox = symbol.getBoundingClientRect();
                    const cellCenterX = cellBox.left + cellBox.width / 2;
                    const cellCenterY = cellBox.top + cellBox.height / 2;
                    const symbolCenterX = symbolBox.left + symbolBox.width / 2;
                    const symbolCenterY = symbolBox.top + symbolBox.height / 2;
                    return {
                        xDelta: Math.abs(cellCenterX - symbolCenterX),
                        yDelta: Math.abs(cellCenterY - symbolCenterY),
                    };
                })(),
            })
            """
        )
        session_snapshot = client.get(
            f"/games/mines/session/{session_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert session_snapshot.status_code == 200
        assert mine_metrics["mineSymbols"] > 0
        assert mine_metrics["mineCentered"] is not None
        assert mine_metrics["mineCentered"]["xDelta"] <= 6
        assert mine_metrics["mineCentered"]["yDelta"] <= 6
        assert session_snapshot.json()["data"]["status"] == "lost"
        browser.close()


@pytest.mark.integration
def test_admin_login_surface_uses_full_width_shell(
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
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")

        metrics = page.evaluate(
            """
            () => {
                const grid = document.querySelector('.dashboard-grid');
                const panel = document.querySelector('.admin-panel-clean');
                const shell = grid?.getBoundingClientRect() ?? null;
                const panelBox = panel?.getBoundingClientRect() ?? null;
                return {
                    gridClass: grid?.className ?? '',
                    shellWidth: shell?.width ?? null,
                    panelWidth: panelBox?.width ?? null,
                };
            }
            """
        )

        assert "dashboard-grid-admin" in metrics["gridClass"]
        assert metrics["shellWidth"] is not None
        assert metrics["panelWidth"] is not None
        assert metrics["panelWidth"] >= metrics["shellWidth"] * 0.9

        browser.close()


@pytest.mark.integration
def test_admin_mines_backoffice_shows_publish_workflow_on_full_width_surface(
    frontend_base_url: str,
    wait_for_frontend,
    create_admin_user,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="browser-admin-backoffice")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
        page.get_by_label("Email").fill(str(admin_user["email"]))
        page.get_by_label("Password").fill(str(admin_user["password"]))
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("button", name="Mines backoffice").click()
        page.wait_for_timeout(800)

        metrics = page.evaluate(
            """
            () => {
                const panel = document.querySelector('.admin-panel-clean');
                const panelBox = panel?.getBoundingClientRect() ?? null;
                const publishButton = Array.from(document.querySelectorAll('button')).find(
                  (button) => button.textContent?.trim() === 'Pubblica live'
                );
                const saveButton = Array.from(document.querySelectorAll('button')).find(
                  (button) => button.textContent?.trim() === 'Salva bozza'
                );
                return {
                  panelWidth: panelBox?.width ?? null,
                  publishVisible: Boolean(
                    publishButton &&
                    publishButton.getBoundingClientRect().width > 0 &&
                    publishButton.getBoundingClientRect().height > 0
                  ),
                  saveVisible: Boolean(
                    saveButton &&
                    saveButton.getBoundingClientRect().width > 0 &&
                    saveButton.getBoundingClientRect().height > 0
                  ),
                };
            }
            """
        )

        assert metrics["panelWidth"] is not None
        assert metrics["panelWidth"] >= 1100
        assert metrics["publishVisible"] is True
        assert metrics["saveVisible"] is True

        browser.close()


@pytest.mark.integration
def test_mines_embed_shows_only_published_mine_choices_for_selected_grid(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    public_config = _load_public_mines_config()
    published_grids = public_config["presentation_config"]["published_grid_sizes"]
    target_grid_size = 25 if 25 in published_grids else published_grids[0]
    expected_values = [
        str(value)
        for value in public_config["presentation_config"]["published_mine_counts"][str(target_grid_size)]
    ]
    target_grid_label = f"{int(target_grid_size ** 0.5)}x{int(target_grid_size ** 0.5)}"

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.goto(f"{frontend_base_url}/mines?embed=1", wait_until="networkidle")
        page.get_by_role("button", name=target_grid_label).click()

        mine_values = page.locator(".field").filter(has_text="Mines").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )

        assert mine_values == expected_values
        assert len(mine_values) <= 5

        browser.close()
