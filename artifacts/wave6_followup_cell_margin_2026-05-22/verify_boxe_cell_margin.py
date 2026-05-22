import json
import re
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"
OUT = Path("artifacts/wave6_followup_cell_margin_2026-05-22")
OUT.mkdir(parents=True, exist_ok=True)


def chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)


def dismiss_boot(page) -> None:
    try:
        page.get_by_role("button", name=re.compile("Salta|Skip", re.I)).click(timeout=12_000)
    except Exception:
        page.wait_for_timeout(8_500)
    try:
        page.get_by_role("button", name=re.compile("Continua|Continue", re.I)).click(timeout=8_000)
    except Exception:
        try:
            page.locator(".game-how-to-play-overlay").click(timeout=2_000)
        except Exception:
            pass
    page.locator(".boxe-pyramid-board").wait_for(timeout=15_000)


def select_config(page, rows: int, difficulty: str) -> None:
    rows_button = page.locator(f'[data-testid="boxe-rows-{rows}"]').first
    difficulty_button = page.locator(f'[data-testid="boxe-difficulty-{difficulty}"]').first
    if rows_button.count() > 0:
        rows_button.click(force=True, timeout=5_000)
    if difficulty_button.count() > 0:
        difficulty_button.click(force=True, timeout=5_000)
    page.wait_for_timeout(120)


def metrics(page, label: str) -> dict:
    return page.evaluate(
        """
        (label) => {
          const stage = document.querySelector('.boxe-stage-board');
          const board = document.querySelector('.boxe-pyramid-board');
          const rows = [...document.querySelectorAll('.boxe-pyramid-row')];
          const cells = [...document.querySelectorAll('.boxe-pyramid-cell')];
          const stageRect = stage.getBoundingClientRect();
          const boardRect = board.getBoundingClientRect();
          const cellRect = cells[0]?.getBoundingClientRect();
          const rects = cells.map((cell) => cell.getBoundingClientRect());
          const union = rects.reduce((acc, rect) => ({
            left: Math.min(acc.left, rect.left),
            right: Math.max(acc.right, rect.right),
            top: Math.min(acc.top, rect.top),
            bottom: Math.max(acc.bottom, rect.bottom),
          }), {left: Infinity, right: -Infinity, top: Infinity, bottom: -Infinity});
          const margins = {
            left: Math.round((union.left - stageRect.left) * 10) / 10,
            right: Math.round((stageRect.right - union.right) * 10) / 10,
            top: Math.round((union.top - stageRect.top) * 10) / 10,
            bottom: Math.round((stageRect.bottom - union.bottom) * 10) / 10,
          };
          return {
            label,
            rows: rows.length,
            cells: cells.length,
            cellWidth: cellRect ? Math.round(cellRect.width * 10) / 10 : null,
            margins,
            minMargin: Math.min(margins.left, margins.right, margins.top, margins.bottom),
            boardOverflowX: board.scrollWidth > board.clientWidth + 1,
            boardOverflowY: board.scrollHeight > board.clientHeight + 1,
            stageOverflowX: stage.scrollWidth > stage.clientWidth + 1,
            stageOverflowY: stage.scrollHeight > stage.clientHeight + 1,
            bodyOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
            boardRect: {width: Math.round(boardRect.width), height: Math.round(boardRect.height)},
            stageRect: {width: Math.round(stageRect.width), height: Math.round(stageRect.height)},
            cssPadding: getComputedStyle(board).padding,
          };
        }
        """,
        label,
    )


def main() -> None:
    rows_values = [4, 5, 6, 7, 8]
    difficulties = ["easy", "medium", "hard"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium_executable())
        page = browser.new_page(viewport={"width": 1097, "height": 827}, reduced_motion="reduce")
        page.goto(f"{BASE}/boxe?title_code=boxe001&mode=demo", wait_until="domcontentloaded", timeout=30_000)
        dismiss_boot(page)
        matrix = []
        for rows in rows_values:
            for difficulty in difficulties:
                select_config(page, rows, difficulty)
                matrix.append(metrics(page, f"desktop 1097x827 rows={rows} difficulty={difficulty} idle"))
        select_config(page, 8, "hard")
        page.screenshot(path=str(OUT / "boxe-1097x827-rows8-hard-idle.png"), full_page=True)
        page.get_by_test_id("boxe-primary-action").click(timeout=10_000)
        page.locator(".boxe-pyramid-row.active").wait_for(timeout=10_000)
        page.screenshot(path=str(OUT / "boxe-1097x827-rows8-hard-active.png"), full_page=True)
        active_metric = metrics(page, "desktop 1097x827 rows=8 hard active")
        page.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        mobile.goto(f"{BASE}/boxe?title_code=boxe001&mode=demo", wait_until="domcontentloaded", timeout=30_000)
        dismiss_boot(mobile)
        select_config(mobile, 8, "hard")
        mobile.screenshot(path=str(OUT / "boxe-mobile-390x844-rows8-hard-idle.png"), full_page=True)
        mobile_metric = metrics(mobile, "mobile 390x844 rows=8 hard idle")
        mobile.close()

        landscape = browser.new_page(viewport={"width": 844, "height": 390}, reduced_motion="reduce")
        landscape.goto(f"{BASE}/boxe?title_code=boxe001&mode=demo", wait_until="domcontentloaded", timeout=30_000)
        dismiss_boot(landscape)
        select_config(landscape, 8, "hard")
        landscape.screenshot(path=str(OUT / "boxe-landscape-844x390-rows8-hard-idle.png"), full_page=True)
        landscape_metric = metrics(landscape, "landscape 844x390 rows=8 hard idle")
        landscape.close()
        browser.close()

    payload = {
        "matrix": matrix,
        "active": active_metric,
        "mobile": mobile_metric,
        "landscape": landscape_metric,
    }
    (OUT / "verification.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "minDesktopMargin": min(item["minMargin"] for item in matrix),
                "maxDesktopOverflow": any(
                    item["boardOverflowX"]
                    or item["boardOverflowY"]
                    or item["stageOverflowX"]
                    or item["stageOverflowY"]
                    or item["bodyOverflowX"]
                    for item in matrix
                ),
                "active": active_metric,
                "mobile": mobile_metric,
                "landscape": landscape_metric,
                "artifactDir": str(OUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
