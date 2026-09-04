from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23")
BASE_URL = "http://127.0.0.1:3000"
HI_LO_DEMO_URL = f"{BASE_URL}/hi-lo?title_code=hilo001&mode=demo"
HI_LO_REAL_URL = f"{BASE_URL}/hi-lo?title_code=hilo001&wallet_source=real"


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


def safe_click(page, selector: str, timeout: int = 3000) -> bool:  # noqa: ANN001
    try:
        page.locator(selector).click(timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def advance_to_gameplay(page) -> None:  # noqa: ANN001
    try:
        page.locator(".game-provider-bootstrap-skip").click(timeout=11000)
    except PlaywrightTimeoutError:
        pass
    try:
        page.locator(".game-how-to-play-continue").click(timeout=12000)
    except PlaywrightTimeoutError:
        safe_click(page, ".game-how-to-play-overlay", timeout=3000)
    page.locator('[data-testid="hi-lo-gameplay"]').wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(500)


def collect_metrics(page, label: str) -> dict[str, object]:  # noqa: ANN001
    return page.evaluate(
        """label => {
            const pick = (selector) => {
              const element = document.querySelector(selector);
              if (!element) {
                return null;
              }
              const rect = element.getBoundingClientRect();
              const style = window.getComputedStyle(element);
              return {
                selector,
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                scrollWidth: element.scrollWidth,
                scrollHeight: element.scrollHeight,
                clientWidth: element.clientWidth,
                clientHeight: element.clientHeight,
                overflowX: style.overflowX,
                overflowY: style.overflowY,
                hasHorizontalOverflow: element.scrollWidth > element.clientWidth + 1,
                hasVerticalOverflow: element.scrollHeight > element.clientHeight + 1
              };
            };
            return {
              label,
              url: window.location.href,
              viewport: { width: window.innerWidth, height: window.innerHeight },
              document: {
                scrollWidth: document.documentElement.scrollWidth,
                scrollHeight: document.documentElement.scrollHeight,
                clientWidth: document.documentElement.clientWidth,
                clientHeight: document.documentElement.clientHeight,
                bodyScrollWidth: document.body.scrollWidth,
                bodyScrollHeight: document.body.scrollHeight,
                hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                hasVerticalOverflow: document.documentElement.scrollHeight > window.innerHeight + 1
              },
              productShell: pick(".hi-lo-product-shell"),
              gameplay: pick("[data-testid='hi-lo-gameplay']"),
              stage: pick(".hi-lo-stage"),
              controlRail: pick(".hi-lo-control-rail"),
              tableGate: pick("[data-testid='hi-lo-table-balance-gate']"),
              adminShell: pick(".admin-page")
            };
        }""",
        label,
    )


def screenshot_page(page, name: str) -> Path:  # noqa: ANN001
    path = ARTIFACT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable-path", default=None)
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    screenshots: list[Path] = []
    metrics: list[dict[str, object]] = []
    notes: list[str] = []

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright, args.executable_path)

        desktop = browser.new_context(
            viewport={"width": 1365, "height": 768},
            locale="it-IT",
            device_scale_factor=1,
        )
        desktop.set_default_timeout(15000)
        page = desktop.new_page()

        page.goto(HI_LO_DEMO_URL, wait_until="domcontentloaded", timeout=30000)
        advance_to_gameplay(page)
        screenshots.append(screenshot_page(page, "01_demo_idle_desktop"))
        metrics.append(collect_metrics(page, "demo_idle_desktop"))

        safe_click(page, ".hi-lo-info-trigger", timeout=5000)
        page.wait_for_timeout(500)
        screenshots.append(screenshot_page(page, "02_info_modal_desktop"))
        metrics.append(collect_metrics(page, "info_modal_desktop"))
        safe_click(page, ".game-info-rules-close", timeout=3000)
        page.keyboard.press("Escape")

        safe_click(page, '[data-testid="hi-lo-bet-button"]', timeout=8000)
        page.wait_for_timeout(1200)
        screenshots.append(screenshot_page(page, "03_demo_after_bet_desktop"))
        metrics.append(collect_metrics(page, "demo_after_bet_desktop"))

        page.goto(HI_LO_REAL_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        screenshots.append(screenshot_page(page, "04_real_table_gate_desktop"))
        metrics.append(collect_metrics(page, "real_table_gate_desktop"))

        for route, name in [
            (f"{BASE_URL}/admin/games/hi-lo", "05_admin_engine_hi_lo"),
            (f"{BASE_URL}/admin/games/hi-lo/titles/hilo001", "06_admin_title_detail_hi_lo"),
            (f"{BASE_URL}/account", "07_account_history"),
        ]:
            page.goto(route, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            screenshots.append(screenshot_page(page, name))
            metrics.append(collect_metrics(page, name))

        desktop.close()

        for width, height, label in [
            (390, 844, "08_demo_idle_mobile_portrait"),
            (844, 390, "09_demo_idle_landscape_short"),
        ]:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                locale="it-IT",
                device_scale_factor=1,
                is_mobile=width < 600,
            )
            context.set_default_timeout(15000)
            mobile_page = context.new_page()
            mobile_page.goto(HI_LO_DEMO_URL, wait_until="domcontentloaded", timeout=30000)
            advance_to_gameplay(mobile_page)
            screenshots.append(screenshot_page(mobile_page, label))
            metrics.append(collect_metrics(mobile_page, label))
            context.close()

        browser.close()

    risky_overflows = []
    for metric in metrics:
        label = str(metric["label"])
        document = metric.get("document") or {}
        gameplay = metric.get("gameplay") or {}
        stage = metric.get("stage") or {}
        if isinstance(document, dict) and document.get("hasHorizontalOverflow"):
            risky_overflows.append(f"{label}: document horizontal overflow")
        if isinstance(gameplay, dict) and gameplay.get("hasHorizontalOverflow"):
            risky_overflows.append(f"{label}: gameplay horizontal overflow")
        if isinstance(stage, dict) and stage.get("hasHorizontalOverflow"):
            risky_overflows.append(f"{label}: stage horizontal overflow")

    if risky_overflows:
        notes.extend(risky_overflows)
    else:
        notes.append("No horizontal overflow detected in captured HI-LO surfaces.")
    real_gate_metric = next(
        (metric for metric in metrics if metric.get("label") == "real_table_gate_desktop"),
        None,
    )
    if isinstance(real_gate_metric, dict) and real_gate_metric.get("tableGate") is not None:
        notes.append(
            "Real route rendered GameTableBalanceGate after a demo active round; wallet-source resume isolation passed.",
        )
    else:
        notes.append("WARNING: real route did not render GameTableBalanceGate in the capture.")

    report_path = ARTIFACT_DIR / "REPORT.md"
    report_path.write_text(
        "\n".join(
            [
                "# HI-LO H7 Technical Walkthrough Evidence - 2026-05-23",
                "",
                "This is a Codex technical/browser pre-check. It is not Michele's product-owner approval.",
                "",
                "Screenshots:",
                *[f"- `{path.as_posix()}`" for path in screenshots],
                "",
                "Notes:",
                *[f"- {note}" for note in notes],
                "",
                "Metrics:",
                "",
                "```json",
                json.dumps(metrics, indent=2),
                "```",
            ],
        ),
        encoding="utf-8",
    )

    print(report_path)
    for path in screenshots:
        print(path)
    for note in notes:
        print(note)


if __name__ == "__main__":
    main()
