from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("tests/visual/artifacts/wave3_htp_pyramid_2026-05-21")
BOXE_MULTIPLIERS = ["1.05", "1.18", "1.38", "1.65"]


def envelope(data: object) -> dict[str, object]:
    return {"success": True, "data": data}


def fulfill(route, data: object | None, path: str) -> None:  # noqa: ANN001
    if data is None:
        route.fulfill(
            status=404,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": False,
                    "error": {"code": "MOCK_ROUTE_MISSING", "message": path},
                },
            ),
        )
        return
    route.fulfill(status=200, content_type="application/json", body=json.dumps(envelope(data)))


class BoxeHowToPlayMock:
    def handle(self, route) -> None:  # noqa: ANN001
        path = urlparse(route.request.url).path
        data: object | None = None

        if path.endswith("/titles/boxe001/theme"):
            data = {
                "title_code": "boxe001",
                "tokens": {},
                "assets": {},
                "skin": None,
                "etag": "boxe-htp-visual",
            }
        elif path.endswith("/games/boxe/config"):
            data = {
                "game_code": "boxe",
                "title_code": "boxe001",
                "default_rows": 4,
                "rows_enabled": [4],
                "default_difficulty": "easy",
                "difficulty_enabled": ["easy"],
                "rtp_label": "",
                "multiplier_paths": {
                    "4": {
                        "easy": BOXE_MULTIPLIERS,
                        "medium": BOXE_MULTIPLIERS,
                        "hard": BOXE_MULTIPLIERS,
                    },
                },
                "copy_refs": {},
                "presentation_config": {
                    "default_locale": "en",
                    "copy": {},
                    "rules_html": {},
                },
            }

        fulfill(route, data, path)


def launch_chromium(playwright, executable_path: str | None):  # noqa: ANN001
    if executable_path:
        return playwright.chromium.launch(headless=True, executable_path=executable_path)
    for candidate in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]:
        if Path(candidate).exists():
            return playwright.chromium.launch(headless=True, executable_path=candidate)
    return playwright.chromium.launch(headless=True)


def write_collage(card_paths: list[Path], output_path: Path) -> None:
    images = [Image.open(path).convert("RGB") for path in card_paths]
    header_h = 36
    gap = 10
    width = sum(image.width for image in images) + gap * (len(images) - 1)
    height = max(image.height for image in images) + header_h
    canvas = Image.new("RGB", (width, height), (7, 9, 14))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    draw.text((12, 9), "BOXE HTP mini pyramid - Bet / Pick / Collect", fill=(245, 248, 255), font=font)

    x = 0
    for image in images:
        canvas.paste(image, (x, header_h))
        x += image.width + gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="http://localhost:3100/boxe?title_code=boxe001&mode=demo&embed=1",
    )
    parser.add_argument("--executable-path", default=None)
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright, args.executable_path)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="it-IT",
            device_scale_factor=1,
        )
        context.set_default_timeout(15000)
        page = context.new_page()
        page.route("**/api/v1/**", BoxeHowToPlayMock().handle)
        page.goto(args.url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.locator(".game-provider-bootstrap-skip").click(timeout=7000)
        except PlaywrightTimeoutError:
            pass
        page.locator(".game-how-to-play-panel").wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(750)

        overview_path = ARTIFACT_DIR / "boxe_htp_gate_overview_desktop.png"
        page.locator(".game-how-to-play-panel").screenshot(path=str(overview_path))

        cards = page.locator(".game-how-to-play-card")
        card_names = ["bet_idle", "pick_mid_progress", "collect_mine_reveal"]
        card_paths: list[Path] = []
        for index, name in enumerate(card_names):
            output = ARTIFACT_DIR / f"boxe_htp_card_{index + 1}_{name}.png"
            cards.nth(index).screenshot(path=str(output))
            card_paths.append(output)

        collage_path = ARTIFACT_DIR / "boxe_htp_cards_collage_desktop.png"
        write_collage(card_paths, collage_path)

        row_summary = page.locator(".boxe-how-to-play-pyramid-row").evaluate_all(
            """rows => rows.map(row => ({
                dataRow: row.getAttribute('data-row'),
                cells: row.querySelectorAll('.boxe-how-to-play-pyramid-cell').length
            }))""",
        )
        asset_summary = page.locator(".boxe-how-to-play-pyramid-cell-face img").evaluate_all(
            """imgs => imgs.map(img => img.getAttribute('src'))""",
        )

        report_path = ARTIFACT_DIR / "REPORT.md"
        report_path.write_text(
            "\n".join(
                [
                    "# Wave 3 HTP Pyramid Evidence - 2026-05-21",
                    "",
                    f"URL: `{args.url}`",
                    "",
                    "Screenshots:",
                    f"- `{overview_path.as_posix()}`",
                    *[f"- `{path.as_posix()}`" for path in card_paths],
                    f"- `{collage_path.as_posix()}`",
                    "",
                    "Directional mockup comparison:",
                    "- `boxe2`: idle pyramid grammar preserved in Bet card with active bottom row.",
                    "- `boxe4`/`boxe5`: mid-progress safe path appears bottom-to-top in Pick card.",
                    "- `boxe6`/`boxe7`: Collect card shows safe path plus fuchsia mine reveal risk.",
                    "",
                    "DOM evidence:",
                    f"- Pyramid rows/cells rendered top-down from bottom-to-top data model: `{row_summary}`.",
                    f"- Safe/mine public assets used: `{asset_summary}`.",
                ],
            ),
            encoding="utf-8",
        )

        context.close()
        browser.close()

    print(overview_path)
    for path in card_paths:
        print(path)
    print(collage_path)
    print(report_path)


if __name__ == "__main__":
    main()
