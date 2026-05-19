from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
import shutil

import pytest


playwright = pytest.importorskip("playwright.sync_api")
Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")


BASELINE_DIR = Path("tests/visual/baselines/boxe_3c")
UPDATE_BASELINES_ENV = "CASINOKING_UPDATE_BOXE_BASELINES"
MAX_DIFF_PIXEL_RATIO = 0.001
CHANNEL_THRESHOLD = 26
VIEWPORTS = [
    ("desktop_1365x768", 1365, 768),
    ("mobile_390x844", 390, 844),
]
SCENARIOS = [
    "idle",
    "active_safe",
    "loss",
    "cashout_win",
    "top_row_win",
]


@pytest.mark.integration
def test_boxe_3c_visual_baselines(frontend_base_url: str, wait_for_frontend) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for visual regression test.")

    update_baselines = os.getenv(UPDATE_BASELINES_ENV) == "1"
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        try:
            for scenario in SCENARIOS:
                for viewport_name, width, height in VIEWPORTS:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.emulate_media(reduced_motion="reduce")
                    _mock_boxe_visual_api(page, scenario=scenario)
                    _open_boxe_visual(page, frontend_base_url)
                    _prepare_visual_scenario(page, scenario)

                    current = Image.open(BytesIO(page.screenshot(full_page=True))).convert("RGBA")
                    baseline_path = BASELINE_DIR / scenario / f"{viewport_name}.png"
                    if update_baselines:
                        baseline_path.parent.mkdir(parents=True, exist_ok=True)
                        current.save(baseline_path)
                    else:
                        baseline = Image.open(baseline_path).convert("RGBA")
                        diff_ratio = _masked_diff_ratio(
                            baseline=baseline,
                            current=current,
                            masks=[],
                        )
                        assert diff_ratio <= MAX_DIFF_PIXEL_RATIO, (
                            f"{scenario}/{viewport_name} visual diff ratio {diff_ratio:.5f} "
                            f"exceeds {MAX_DIFF_PIXEL_RATIO:.5f}"
                        )
                    page.close()
        finally:
            browser.close()


def _open_boxe_visual(page, frontend_base_url: str) -> None:
    page.add_init_script(
        """
        window.localStorage.setItem('casinoking.access_token', 'boxe-visual-token');
        window.localStorage.setItem('casinoking.email', 'boxe-visual@example.com');
        """
    )
    page.goto(
        f"{frontend_base_url}/boxe?title_code=boxe001&mode=demo",
        wait_until="networkidle",
    )
    page.locator(".game-provider-bootstrap-skip").click()
    page.get_by_role("button", name="Continua").click()
    page.get_by_test_id("boxe-table-balance-gate").get_by_role(
        "button",
        name="Continua",
    ).click()
    page.get_by_test_id("boxe-gameplay").wait_for()


def _prepare_visual_scenario(page, scenario: str) -> None:
    page.get_by_test_id("boxe-rows-4").click()
    page.get_by_test_id("boxe-difficulty-easy").click()
    page.get_by_test_id("boxe-bet-input").fill("1")

    if scenario == "idle":
        return

    page.get_by_test_id("boxe-primary-action").click()
    page.get_by_text("active").wait_for()

    if scenario == "active_safe":
        page.get_by_test_id("boxe-cell-0-0").click()
        page.locator(".boxe-pyramid-cell.safe").wait_for()
        return

    if scenario == "loss":
        page.get_by_test_id("boxe-cell-0-1").click()
        page.locator(".boxe-pyramid-cell.mine").wait_for()
        return

    if scenario == "cashout_win":
        page.get_by_test_id("boxe-cell-0-0").click()
        page.locator(".boxe-pyramid-cell.safe").wait_for()
        page.get_by_test_id("boxe-primary-action").click()
        page.get_by_test_id("boxe-win-celebration").wait_for()
        return

    if scenario == "top_row_win":
        for row in range(4):
            page.get_by_test_id(f"boxe-cell-{row}-0").click()
        page.get_by_test_id("boxe-win-celebration").wait_for()
        return

    raise AssertionError(f"Unknown BOXE visual scenario: {scenario}")


def _mock_boxe_visual_api(page, *, scenario: str) -> None:
    page.route("**/api/v1/titles/boxe001/theme", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "success": True,
            "data": {
                "title_code": "boxe001",
                "tokens": {},
                "assets": {},
                "skin": None,
                "etag": "boxe-visual",
            },
        }),
    ))
    page.route("**/api/v1/games/boxe/config?*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "success": True,
            "data": {
                "game_code": "boxe",
                "title_code": "boxe001",
                "default_rows": 4,
                "rows_enabled": [4, 5, 6, 7, 8],
                "default_difficulty": "easy",
                "difficulty_enabled": ["easy", "medium", "hard"],
                "rtp_label": "98%",
                "multiplier_paths": {
                    "4": {"easy": ["1.37", "1.75", "2.24", "2.87"]},
                    "5": {"easy": ["1.46", "1.87", "2.39", "3.05", "3.91"]},
                    "6": {"easy": ["1.55", "1.99", "2.54", "3.25", "4.16", "5.32"]},
                    "7": {"easy": ["1.65", "2.11", "2.71", "3.46", "4.43", "5.66", "7.25"]},
                    "8": {"easy": ["1.76", "2.25", "2.88", "3.68", "4.71", "6.03", "7.72", "9.87"]},
                },
                "copy_refs": {"rules": "boxe.rules", "failure": "boxe.failure"},
            },
        }),
    ))
    page.route("**/api/v1/games/boxe/start", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "success": True,
            "data": {
                "session_id": "boxe-visual-session",
                "round_id": "boxe-visual-round",
                "multipliers": ["1.37", "1.75", "2.24", "2.87"],
                "status": "active",
                "server_seed_hash": "boxe-visual-seed",
            },
        }),
    ))
    page.route("**/api/v1/games/boxe/reveal", lambda route: _fulfill_visual_reveal(route, scenario))
    page.route("**/api/v1/games/boxe/cashout", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "success": True,
            "data": {
                "round_id": "boxe-visual-round",
                "payout": "1.37",
                "status": "completed_cashout",
            },
        }),
    ))


def _fulfill_visual_reveal(route, scenario: str) -> None:
    payload = json.loads(route.request.post_data or "{}")
    row = int(payload.get("row", 0))
    if scenario == "loss":
        data = {
            "round_id": "boxe-visual-round",
            "outcome": "mine",
            "multiplier": "0",
            "payout": "0",
            "next_step_options": [],
            "status": "failed_mine",
        }
    elif scenario == "top_row_win" and row == 3:
        data = {
            "round_id": "boxe-visual-round",
            "outcome": "top_row",
            "multiplier": "2.87",
            "payout": "2.87",
            "next_step_options": [],
            "status": "completed_top_row",
        }
    else:
        multiplier = ["1.37", "1.75", "2.24", "2.87"][row]
        data = {
            "round_id": "boxe-visual-round",
            "outcome": "safe",
            "multiplier": multiplier,
            "payout": multiplier,
            "next_step_options": [{"row": row + 1, "position": position} for position in range(3)] if row < 3 else [],
            "status": "row_revealed",
        }
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"success": True, "data": data}),
    )


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


def _masked_diff_ratio(
    *,
    baseline,
    current,
    masks: list[tuple[int, int, int, int]],
) -> float:
    assert baseline.size == current.size
    baseline = baseline.copy()
    current = current.copy()
    for image in (baseline, current):
        draw = ImageDraw.Draw(image)
        for mask in masks:
            draw.rectangle(mask, fill=(0, 0, 0, 255))

    total = baseline.size[0] * baseline.size[1]
    changed = 0
    for expected, actual in zip(baseline.getdata(), current.getdata()):
        if max(abs(expected[index] - actual[index]) for index in range(4)) > CHANNEL_THRESHOLD:
            changed += 1
    return changed / total
