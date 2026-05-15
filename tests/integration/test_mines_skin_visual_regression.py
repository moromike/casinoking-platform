from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
import shutil
from uuid import uuid4

import pytest


playwright = pytest.importorskip("playwright.sync_api")
Image = pytest.importorskip("PIL.Image")
ImageDraw = pytest.importorskip("PIL.ImageDraw")
PlaywrightTimeoutError = playwright.TimeoutError


BASELINE_DIR = Path("tests/visual/baselines/mines_classic")
BOOT_2A_BASELINE_DIR = Path("tests/visual/baselines/boot_2a")
MAX_DIFF_PIXEL_RATIO = 0.001
CHANNEL_THRESHOLD = 26
VIEWPORTS = [
    ("desktop_1440x900", 1440, 900, [(48, 18, 136, 70)]),
    ("mobile_375x812", 375, 812, [(46, 10, 128, 62)]),
]
BOOT_2A_SCENARIOS = [
    "provider_intro",
    "how_to_play_gate",
    "table_balance_gate",
    "config_error_overlay",
    "mobile_guard",
]


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


@pytest.mark.integration
def test_mines_classic_default_skin_visual_regression(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for visual regression test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        try:
            for name, width, height, masks in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.emulate_media(reduced_motion="reduce")
                page.goto(
                    f"{frontend_base_url}/mines?title_code=mines_classic&mode=demo&embed=1",
                    wait_until="networkidle",
                )
                try:
                    page.locator(".mines-provider-bootstrap-skip").click(timeout=10_000)
                except PlaywrightTimeoutError:
                    pass
                try:
                    page.locator(".mines-how-to-play-continue").click(timeout=10_000)
                except PlaywrightTimeoutError:
                    pass
                page.locator(".mines-stage-board").wait_for(state="visible", timeout=15_000)
                page.wait_for_timeout(800)

                current = Image.open(BytesIO(page.screenshot(full_page=True))).convert("RGBA")
                baseline = Image.open(BASELINE_DIR / f"{name}.png").convert("RGBA")
                diff_ratio = _masked_diff_ratio(
                    baseline=baseline,
                    current=current,
                    masks=masks,
                )
                assert diff_ratio <= MAX_DIFF_PIXEL_RATIO, (
                    f"{name} visual diff ratio {diff_ratio:.5f} exceeds "
                    f"{MAX_DIFF_PIXEL_RATIO:.5f}"
                )
                page.close()
        finally:
            browser.close()


@pytest.mark.integration
def test_mines_boot_2a_visual_baselines(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for visual regression test.")

    update_baselines = os.getenv("CASINOKING_UPDATE_BOOT_2A_BASELINES") == "1"
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_visual_{uuid4().hex[:8]}",
            display_name="BOOT 2A Visual Baseline Test",
        )["title_code"]
    )
    player = create_authenticated_player(prefix="boot-2a-visual-player")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        try:
            for scenario in BOOT_2A_SCENARIOS:
                for viewport_name, width, height, masks in VIEWPORTS:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.emulate_media(reduced_motion="reduce")
                    _prepare_boot_2a_scenario(
                        page,
                        scenario=scenario,
                        frontend_base_url=frontend_base_url,
                        title_code=title_code,
                        access_token=str(player["access_token"]),
                        email=str(player["email"]),
                    )
                    current = Image.open(BytesIO(page.screenshot(full_page=True))).convert("RGBA")
                    baseline_path = BOOT_2A_BASELINE_DIR / scenario / f"{viewport_name}.png"
                    if update_baselines:
                        baseline_path.parent.mkdir(parents=True, exist_ok=True)
                        current.save(baseline_path)
                    else:
                        baseline = Image.open(baseline_path).convert("RGBA")
                        diff_ratio = _masked_diff_ratio(
                            baseline=baseline,
                            current=current,
                            masks=[*masks, *_boot_2a_masks(scenario, width, height)],
                        )
                        assert diff_ratio <= MAX_DIFF_PIXEL_RATIO, (
                            f"{scenario}/{viewport_name} visual diff ratio {diff_ratio:.5f} "
                            f"exceeds {MAX_DIFF_PIXEL_RATIO:.5f}"
                        )
                    page.close()
        finally:
            browser.close()


def _prepare_boot_2a_scenario(
    page,
    *,
    scenario: str,
    frontend_base_url: str,
    title_code: str,
    access_token: str,
    email: str,
) -> None:
    if scenario == "provider_intro":
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-provider-bootstrap").wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(300)
        return

    if scenario == "how_to_play_gate":
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-provider-bootstrap-skip").click(timeout=15_000)
        page.locator(".mines-how-to-play-overlay").wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(300)
        return

    if scenario == "table_balance_gate":
        _seed_player_storage(page, access_token=access_token, email=email)
        _route_mocked_access_session(page, title_code=title_code)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&wallet_source=real&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-launch-gate").wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(300)
        return

    if scenario == "config_error_overlay":
        _route_failed_mines_config(page)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-error-dialog").wait_for(state="visible", timeout=15_000)
        page.wait_for_timeout(300)
        return

    if scenario == "mobile_guard":
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-provider-bootstrap-skip").click(timeout=15_000)
        page.locator(".mines-how-to-play-continue").click(timeout=15_000)
        page.locator(".mines-board, .mines-viewport-guard").first.wait_for(timeout=15_000)
        page.wait_for_timeout(300)
        return

    raise AssertionError(f"Unknown BOOT-2A visual scenario: {scenario}")


def _seed_player_storage(page, *, access_token: str, email: str) -> None:
    page.add_init_script(
        f"""
        window.localStorage.setItem('casinoking.access_token', {json.dumps(access_token)});
        window.localStorage.setItem('casinoking.email', {json.dumps(email)});
        window.localStorage.removeItem('casinoking.current_session_id');
        """
    )


def _route_mocked_access_session(page, *, title_code: str) -> None:
    def handle_access_sessions(route) -> None:
        if route.request.method != "POST":
            route.continue_()
            return
        payload = json.loads(route.request.post_data or "{}")
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "id": f"boot-2a-visual-{title_code}",
                        "user_id": "boot-2a-visual-user",
                        "game_code": payload.get("game_code", "mines"),
                        "title_code": payload.get("title_code", title_code),
                        "site_code": "casinoking",
                        "started_at": "2026-05-15T00:00:00+00:00",
                        "last_activity_at": "2026-05-15T00:00:00+00:00",
                        "ended_at": None,
                        "status": "active",
                    },
                }
            ),
        )

    page.route("**/api/v1/access-sessions", handle_access_sessions)


def _route_failed_mines_config(page) -> None:
    def handle_config(route) -> None:
        route.fulfill(
            status=503,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": False,
                    "error": {
                        "code": "CONFIG_UNAVAILABLE",
                        "message": "BOOT-2A simulated config failure",
                    },
                }
            ),
        )

    page.route("**/api/v1/games/mines/config?*", handle_config)


def _boot_2a_masks(scenario: str, width: int, height: int) -> list[tuple[int, int, int, int]]:
    if scenario == "provider_intro":
        return [(0, max(0, height - 120), width, height)]
    return []


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
