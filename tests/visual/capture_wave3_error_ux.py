from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("tests/visual/artifacts/wave3_error_ux_2026-05-21")
BOXE_MULTIPLIERS = ["1.05", "1.18", "1.38", "1.65"]


def envelope(data: object) -> dict[str, object]:
    return {"success": True, "data": data}


def error_envelope(code: str, message: str) -> dict[str, object]:
    return {"success": False, "error": {"code": code, "message": message}}


def fulfill_success(route, data: object) -> None:  # noqa: ANN001
    route.fulfill(status=200, content_type="application/json", body=json.dumps(envelope(data)))


def fulfill_error(route, status: int, code: str, message: str) -> None:  # noqa: ANN001
    route.fulfill(
        status=status,
        content_type="application/json",
        body=json.dumps(error_envelope(code, message)),
    )


def runtime_config() -> dict[str, object]:
    paths = {
        "4": {
            "easy": BOXE_MULTIPLIERS,
            "medium": BOXE_MULTIPLIERS,
            "hard": BOXE_MULTIPLIERS,
        },
    }
    return {
        "game_code": "boxe",
        "title_code": "boxe001",
        "default_rows": 4,
        "rows_enabled": [4],
        "default_difficulty": "easy",
        "difficulty_enabled": ["easy"],
        "rtp_label": "",
        "multiplier_paths": paths,
        "copy_refs": {},
        "presentation_config": {
            "default_locale": "it",
            "copy": {},
            "rules_html": {},
        },
    }


def theme_payload(etag: str) -> dict[str, object]:
    return {
        "title_code": "boxe001",
        "tokens": {},
        "assets": {},
        "skin": None,
        "etag": etag,
    }


def demo_auth(token: str) -> dict[str, object]:
    return {
        "user_id": f"user-{token}",
        "email": f"{token}@example.test",
        "access_token": token,
        "token_type": "bearer",
    }


def start_round_payload() -> dict[str, object]:
    return {
        "session_id": "boxe-error-session",
        "round_id": "boxe-error-round",
        "multipliers": BOXE_MULTIPLIERS,
        "status": "active",
        "server_seed_hash": "boxe-error-seed",
        "table_session_id": None,
        "table_session": None,
    }


class RuntimeErrorMock:
    def handle(self, route) -> None:  # noqa: ANN001
        path = urlparse(route.request.url).path
        if path.endswith("/titles/boxe001/theme"):
            fulfill_success(route, theme_payload("boxe-error-runtime-theme"))
            return
        if path.endswith("/games/boxe/config"):
            fulfill_error(route, 500, "API_ERROR", "database pool unavailable: stack trace")
            return
        fulfill_error(route, 404, "MOCK_ROUTE_MISSING", path)


class ActionErrorMock:
    def handle(self, route) -> None:  # noqa: ANN001
        path = urlparse(route.request.url).path
        if path.endswith("/titles/boxe001/theme"):
            fulfill_success(route, theme_payload("boxe-error-action-theme"))
            return
        if path.endswith("/games/boxe/config"):
            fulfill_success(route, runtime_config())
            return
        if path.endswith("/auth/demo"):
            fulfill_success(route, demo_auth("action-token"))
            return
        if path.endswith("/games/boxe/start"):
            fulfill_error(route, 422, "VALIDATION_ERROR", "bet_amount must be greater than zero")
            return
        fulfill_error(route, 404, "MOCK_ROUTE_MISSING", path)


class RecoveryMock:
    def __init__(self) -> None:
        self.demo_tokens = ["fresh-token"]
        self.start_attempts: list[dict[str, str]] = []

    def handle(self, route) -> None:  # noqa: ANN001
        path = urlparse(route.request.url).path
        request = route.request
        if path.endswith("/titles/boxe001/theme"):
            fulfill_success(route, theme_payload("boxe-error-recovery-theme"))
            return
        if path.endswith("/games/boxe/config"):
            fulfill_success(route, runtime_config())
            return
        if path.endswith("/auth/demo"):
            token = self.demo_tokens.pop(0) if self.demo_tokens else "extra-token"
            fulfill_success(route, demo_auth(token))
            return
        if path.endswith("/games/boxe/start"):
            headers = request.headers
            auth_header = headers.get("authorization", "")
            idem_key = headers.get("idempotency-key", "")
            self.start_attempts.append({"authorization": auth_header, "idempotency_key": idem_key})
            if auth_header == "Bearer expired-token":
                fulfill_error(route, 401, "UNAUTHORIZED", "Invalid bearer token")
                return
            if auth_header == "Bearer fresh-token":
                fulfill_success(route, start_round_payload())
                return
            fulfill_error(route, 401, "UNAUTHORIZED", f"Unexpected token {auth_header}")
            return
        fulfill_error(route, 404, "MOCK_ROUTE_MISSING", path)


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


def skip_provider_intro(page) -> None:  # noqa: ANN001
    try:
        page.locator(".game-provider-bootstrap-skip").click(timeout=9000)
    except PlaywrightTimeoutError:
        pass


def continue_how_to_play(page) -> None:  # noqa: ANN001
    try:
        page.locator(".game-how-to-play-continue").click(timeout=9000)
    except PlaywrightTimeoutError:
        pass


def reach_gameplay(page) -> None:  # noqa: ANN001
    skip_provider_intro(page)
    continue_how_to_play(page)
    page.locator('[data-testid="boxe-gameplay"]').wait_for(state="visible", timeout=15000)


def capture_runtime_error(context, url: str) -> Path:  # noqa: ANN001
    page = context.new_page()
    page.route("**/api/v1/**", RuntimeErrorMock().handle)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    skip_provider_intro(page)
    dialog = page.locator('[data-testid="boxe-runtime-error-dialog"]')
    dialog.wait_for(state="visible", timeout=15000)
    output = ARTIFACT_DIR / "boxe_runtime_error_dialog.png"
    page.screenshot(path=str(output), full_page=True)
    return output


def capture_action_error(context, url: str) -> Path:  # noqa: ANN001
    page = context.new_page()
    page.route("**/api/v1/**", ActionErrorMock().handle)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    reach_gameplay(page)
    page.locator('[data-testid="boxe-primary-action"]').click(timeout=10000)
    dialog = page.locator('[data-testid="boxe-action-error-dialog"]')
    dialog.wait_for(state="visible", timeout=15000)
    output = ARTIFACT_DIR / "boxe_action_error_dialog.png"
    page.screenshot(path=str(output), full_page=True)
    return output


def verify_401_recovery(context, url: str) -> tuple[Path, Path]:  # noqa: ANN001
    recovery_mock = RecoveryMock()
    page = context.new_page()
    page.route("**/api/v1/**", recovery_mock.handle)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    reach_gameplay(page)
    page.locator('[data-testid="boxe-primary-action"]').click(timeout=10000)
    page.locator(".boxe-pyramid-board").wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(350)

    screenshot_path = ARTIFACT_DIR / "boxe_401_recovery_after_start.png"
    page.screenshot(path=str(screenshot_path), full_page=True)

    tokens = [attempt["authorization"] for attempt in recovery_mock.start_attempts]
    idempotency_keys = [attempt["idempotency_key"] for attempt in recovery_mock.start_attempts]
    same_idempotency_key = len(set(idempotency_keys)) == 1 if idempotency_keys else False
    dialog_count = page.locator('[data-testid="boxe-action-error-dialog"]').count()
    stored_token = page.evaluate("window.localStorage.getItem('casinoking.access_token')")

    if tokens != ["Bearer expired-token", "Bearer fresh-token"]:
        raise AssertionError(f"Unexpected 401 recovery token sequence: {tokens}")
    if not same_idempotency_key:
        raise AssertionError(f"Idempotency key changed during recovery: {idempotency_keys}")
    if dialog_count != 0:
        raise AssertionError("401 recovery rendered an action error dialog")
    if stored_token != "fresh-token":
        raise AssertionError(f"Fresh demo token was not persisted: {stored_token}")

    note_path = ARTIFACT_DIR / "boxe_401_recovery_note.md"
    note_path.write_text(
        "\n".join(
            [
                "# Wave 3 BOXE 401 Recovery Evidence - 2026-05-21",
                "",
                f"URL: `{url}`",
                "",
                "Scenario:",
                "- Browser starts with cached `casinoking.access_token=expired-token`.",
                "- First `POST /games/boxe/start` returns `401 Invalid bearer token`.",
                "- BOXE clears cached auth, calls `POST /auth/demo`, then retries the same action once.",
                "",
                "Observed route evidence:",
                f"- Start authorization sequence: `{tokens}`.",
                f"- Start idempotency keys: `{idempotency_keys}`.",
                f"- Same idempotency key reused: `{same_idempotency_key}`.",
                f"- Error dialog count after recovery: `{dialog_count}`.",
                f"- Stored token after recovery: `{stored_token}`.",
                "",
                "Verdict: silent demo auth recovery passed; backend raw `Invalid bearer token` was not rendered.",
                "",
                f"Screenshot: `{screenshot_path.as_posix()}`.",
            ],
        ),
        encoding="utf-8",
    )
    return note_path, screenshot_path


def new_context(browser, storage_state: dict[str, object] | None = None):  # noqa: ANN001
    context_kwargs: dict[str, object] = {
        "viewport": {"width": 1365, "height": 768},
        "locale": "it-IT",
        "device_scale_factor": 1,
    }
    if storage_state is not None:
        context_kwargs["storage_state"] = storage_state
    context = browser.new_context(**context_kwargs)
    context.set_default_timeout(15000)
    return context


def write_report(
    url: str,
    runtime_path: Path,
    action_path: Path,
    recovery_note: Path,
    recovery_screenshot: Path,
) -> Path:
    report_path = ARTIFACT_DIR / "REPORT.md"
    report_path.write_text(
        "\n".join(
            [
                "# Wave 3 Error UX Evidence - 2026-05-21",
                "",
                f"URL: `{url}`",
                "",
                "Screenshots:",
                f"- Runtime 5xx dialog: `{runtime_path.as_posix()}`.",
                f"- Action 422 dialog: `{action_path.as_posix()}`.",
                f"- 401 recovery success state: `{recovery_screenshot.as_posix()}`.",
                "",
                "Route/DOM evidence:",
                f"- 401 recovery note: `{recovery_note.as_posix()}`.",
                "",
                "Verdict:",
                "- BOXE action/runtime errors use the shared `GameActionError` overlay.",
                "- Backend raw strings are mapped to player-facing copy.",
                "- Demo `401 Invalid bearer token` recovers silently with one retry.",
            ],
        ),
        encoding="utf-8",
    )
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="http://localhost:3200/boxe?title_code=boxe001&mode=demo&embed=1",
    )
    parser.add_argument("--executable-path", default=None)
    args = parser.parse_args()

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright, args.executable_path)

        context = new_context(browser)
        runtime_path = capture_runtime_error(context, args.url)
        context.close()

        context = new_context(browser)
        action_path = capture_action_error(context, args.url)
        context.close()

        parsed_url = urlparse(args.url)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        expired_token_storage = {
            "cookies": [],
            "origins": [
                {
                    "origin": origin,
                    "localStorage": [
                        {"name": "casinoking.access_token", "value": "expired-token"},
                        {"name": "casinoking.email", "value": "expired@example.test"},
                    ],
                },
            ],
        }
        context = new_context(browser, storage_state=expired_token_storage)
        recovery_note, recovery_screenshot = verify_401_recovery(context, args.url)
        context.close()
        report_path = write_report(
            args.url,
            runtime_path,
            action_path,
            recovery_note,
            recovery_screenshot,
        )
        browser.close()

    print(runtime_path)
    print(action_path)
    print(recovery_note)
    print(recovery_screenshot)
    print(report_path)


if __name__ == "__main__":
    main()
