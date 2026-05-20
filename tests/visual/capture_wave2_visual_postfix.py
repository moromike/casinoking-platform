from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ARTIFACT_DIR = Path("tests/visual/artifacts/wave2_visual_postfix_2026-05-20")
MINES_MULTIPLIERS = ["1.10", "1.25", "1.43", "1.64", "1.88", "2.17", "2.50", "2.89"]
BOXE_MULTIPLIERS = ["1.05", "1.18", "1.38", "1.65", "2.10", "2.80", "3.75", "5.20"]

STATES = [
    ("idle_desktop", 1365, 768, "idle"),
    ("active_desktop", 1365, 768, "active"),
    ("win_desktop", 1365, 768, "win"),
    ("idle_mobile_portrait", 390, 844, "idle"),
    ("active_mobile_portrait", 390, 844, "active"),
    ("landscape_rotation", 844, 390, "idle"),
]


def envelope(data: object) -> dict[str, object]:
    return {"success": True, "data": data}


def error_envelope(path: str) -> dict[str, object]:
    return {
        "success": False,
        "error": {"code": "MOCK_ROUTE_MISSING", "message": path},
    }


def now_iso() -> str:
    return "2026-05-20T18:05:00.000Z"


class MinesMock:
    def __init__(self) -> None:
        self.session_id = "mines-visual-session"
        self.status = "active"
        self.revealed: list[int] = []
        self.balance = "100"
        self.bet = "5"
        self.closed_at: str | None = None

    def session(self) -> dict[str, object]:
        safe_count = len(self.revealed)
        potential = MINES_MULTIPLIERS[max(safe_count - 1, 0)] if safe_count else "0"
        return {
            "game_session_id": self.session_id,
            "status": self.status,
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": self.bet,
            "title_code": "mines_classic",
            "site_code": "casinoking",
            "wallet_type": "demo",
            "access_session_id": None,
            "table_session_id": None,
            "safe_reveals_count": safe_count,
            "revealed_cells": list(self.revealed),
            "multiplier_current": potential,
            "potential_payout": potential,
            "wallet_balance_after_start": "95",
            "fairness_version": "visual-mock",
            "nonce": 1,
            "server_seed_hash": "visual-server-seed-hash",
            "board_hash": "visual-board-hash",
            "ledger_transaction_id": "visual-ledger",
            "created_at": now_iso(),
            "closed_at": self.closed_at,
        }

    def handle(self, route) -> None:  # noqa: ANN001 - Playwright route type is runtime-only here.
        request = route.request
        path = urlparse(request.url).path
        data: object | None = None

        if path.endswith("/titles/mines_classic/theme"):
            data = {
                "title_code": "mines_classic",
                "tokens": {},
                "assets": {},
                "skin": None,
                "etag": "mines-visual-theme",
            }
        elif path.endswith("/games/mines/config"):
            data = {
                "game_code": "mines",
                "supported_grid_sizes": [25],
                "supported_mine_counts": {"25": [3]},
                "payout_ladders": {"25": {"3": MINES_MULTIPLIERS}},
                "fairness_version": "visual-mock",
                "presentation_config": {
                    "published_grid_sizes": [25],
                    "published_mine_counts": {"25": [3]},
                    "default_mine_counts": {"25": 3},
                    "rules_sections": {},
                    "ui_labels": {},
                    "i18n": {
                        "resolved_locale": "en",
                        "default_locale": "en",
                        "copy": {},
                        "rules_sections": {},
                    },
                    "board_assets": {},
                },
            }
        elif path.endswith("/games/mines/fairness/current"):
            data = {
                "fairness_version": "visual-mock",
                "fairness_phase": "active",
                "active_server_seed_hash": "visual-server-seed-hash",
                "user_verifiable": True,
            }
        elif path.endswith("/demo/token"):
            data = {"anonymous_token": "visual-demo-anon"}
        elif path.endswith("/demo/launch"):
            data = {
                "game_launch_token": "visual-demo-launch",
                "expires_at": "2099-01-01T00:00:00.000Z",
                "anonymous_id": "visual-anon",
                "balance_chips": self.balance,
            }
        elif path.endswith("/games/mines/start"):
            try:
                body = json.loads(request.post_data or "{}")
                self.bet = str(body.get("bet_amount") or self.bet)
            except json.JSONDecodeError:
                pass
            self.status = "active"
            self.revealed = []
            self.closed_at = None
            self.balance = "95"
            data = {
                "game_session_id": self.session_id,
                "mode": "demo",
                "wallet_balance_after": self.balance,
            }
        elif re.search(r"/games/mines/session/[^/]+/fairness$", path):
            data = {
                "fairness_version": "visual-mock",
                "nonce": 1,
                "server_seed_hash": "visual-server-seed-hash",
                "board_hash": "visual-board-hash",
                "user_verifiable": True,
            }
        elif re.search(r"/games/mines/session/[^/]+/replay$", path):
            data = {"rounds": []}
        elif re.search(r"/games/mines/session/[^/]+$", path):
            data = self.session()
        elif path.endswith("/games/mines/reveal"):
            try:
                body = json.loads(request.post_data or "{}")
                cell_index = int(body.get("cell_index", 0))
            except (json.JSONDecodeError, TypeError, ValueError):
                cell_index = 0
            if cell_index not in self.revealed:
                self.revealed.append(cell_index)
            data = {
                "result": "safe",
                "status": "active",
                "payout_amount": MINES_MULTIPLIERS[0],
                "mine_positions": [],
            }
        elif path.endswith("/games/mines/cashout"):
            self.status = "won"
            self.closed_at = now_iso()
            self.balance = "100.50"
            data = {
                "game_session_id": self.session_id,
                "status": "won",
                "payout_amount": "5.50",
                "wallet_balance_after": self.balance,
                "mine_positions": [7, 13, 21],
                "mode": "demo",
            }

        fulfill(route, data, path)


class BoxeMock:
    def __init__(self) -> None:
        self.round_id = "boxe-visual-round"
        self.session_id = "boxe-visual-session"
        self.payout = "0"

    def handle(self, route) -> None:  # noqa: ANN001 - Playwright route type is runtime-only here.
        path = urlparse(route.request.url).path
        data: object | None = None

        if path.endswith("/titles/boxe001/theme"):
            data = {
                "title_code": "boxe001",
                "tokens": {},
                "assets": {},
                "skin": None,
                "etag": "boxe-visual-theme",
            }
        elif path.endswith("/games/boxe/config"):
            paths = {
                str(rows): {
                    "easy": BOXE_MULTIPLIERS[:rows],
                    "medium": BOXE_MULTIPLIERS[:rows],
                    "hard": BOXE_MULTIPLIERS[:rows],
                }
                for rows in [4, 6, 8]
            }
            data = {
                "game_code": "boxe",
                "title_code": "boxe001",
                "default_rows": 4,
                "rows_enabled": [4, 6, 8],
                "default_difficulty": "easy",
                "difficulty_enabled": ["easy", "medium", "hard"],
                "rtp_label": "",
                "multiplier_paths": paths,
                "copy_refs": {},
                "presentation_config": {
                    "default_locale": "en",
                    "copy": {},
                    "rules_html": {},
                },
            }
        elif path.endswith("/auth/demo"):
            data = {
                "user_id": "visual-boxe-user",
                "email": "visual-boxe@example.test",
                "access_token": "visual-boxe-token",
                "token_type": "bearer",
            }
        elif path.endswith("/games/boxe/start"):
            self.payout = "0"
            data = {
                "session_id": self.session_id,
                "round_id": self.round_id,
                "multipliers": BOXE_MULTIPLIERS[:4],
                "status": "active",
                "server_seed_hash": "boxe-visual-server-seed",
                "table_session_id": None,
                "table_session": None,
            }
        elif path.endswith("/games/boxe/reveal"):
            self.payout = "5.25"
            data = {
                "round_id": self.round_id,
                "outcome": "safe",
                "multiplier": "1.05",
                "payout": self.payout,
                "next_step_options": [{"row": 1, "position": index} for index in range(4)],
                "status": "row_revealed",
            }
        elif path.endswith("/games/boxe/cashout"):
            data = {
                "round_id": self.round_id,
                "payout": self.payout or "5.25",
                "status": "completed_cashout",
                "platform_round_id": "boxe-platform-round",
                "ledger_transaction_id": "boxe-ledger",
            }

        fulfill(route, data, path)


def fulfill(route, data: object | None, path: str) -> None:  # noqa: ANN001
    if data is None:
        print(f"unhandled mock route: {path}")
        route.fulfill(
            status=404,
            content_type="application/json",
            body=json.dumps(error_envelope(path)),
        )
        return
    route.fulfill(status=200, content_type="application/json", body=json.dumps(envelope(data)))


def dismiss_gates(page) -> None:  # noqa: ANN001
    page.wait_for_load_state("domcontentloaded")
    try:
        page.locator(".game-provider-bootstrap-skip").click(timeout=4500)
    except PlaywrightTimeoutError:
        pass
    try:
        page.locator(".game-how-to-play-continue").click(timeout=4500)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(350)


def start_round(page, game: str) -> None:  # noqa: ANN001
    if game == "mines":
        try:
            page.locator("#bet-amount-standalone").fill("5", timeout=2000)
        except PlaywrightTimeoutError:
            pass
        page.get_by_role("button", name=re.compile(r"^(Bet|Punta|Apostar|Setzen)$", re.I)).first.click(timeout=5000)
        page.wait_for_function(
            "document.querySelectorAll('.board-cell:not(:disabled)').length > 0",
            timeout=6000,
        )
    else:
        try:
            page.locator("#boxe-bet-input").fill("5", timeout=2000)
        except PlaywrightTimeoutError:
            pass
        page.locator('[data-testid="boxe-primary-action"]').click(timeout=5000)
        page.wait_for_function(
            "document.querySelectorAll('.boxe-pyramid-cell:not(:disabled)').length > 0",
            timeout=6000,
        )
    page.wait_for_timeout(300)


def win_round(page, game: str) -> None:  # noqa: ANN001
    start_round(page, game)
    if game == "mines":
        page.locator(".board-cell:not(:disabled)").first.click(timeout=5000)
        page.wait_for_function(
            "document.querySelectorAll('.board-cell.revealed-safe').length > 0",
            timeout=6000,
        )
        page.get_by_role("button", name=re.compile(r"Collect|Incassa|COLLECT|Cash", re.I)).first.click(timeout=5000)
    else:
        page.locator('[data-testid="boxe-cell-0-0"]').click(timeout=5000)
        page.wait_for_function(
            "document.querySelectorAll('.boxe-pyramid-cell.safe').length > 0",
            timeout=6000,
        )
        page.locator('[data-testid="boxe-primary-action"]').click(timeout=5000)
    page.wait_for_timeout(900)


def capture_single(browser, game: str, url: str, name: str, width: int, height: int, target_state: str, raw_dir: Path) -> Path:  # noqa: ANN001
    context = browser.new_context(
        viewport={"width": width, "height": height},
        locale="en-US",
        device_scale_factor=1,
    )
    context.set_default_timeout(15000)
    mock = MinesMock() if game == "mines" else BoxeMock()
    page = context.new_page()
    page.route("**/api/v1/**", mock.handle)
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    dismiss_gates(page)
    if target_state == "active":
        start_round(page, game)
    elif target_state == "win":
        win_round(page, game)
    page.wait_for_timeout(500)
    raw_path = raw_dir / f"{game}_{name}.png"
    page.screenshot(path=str(raw_path), full_page=False)
    context.close()
    return raw_path


def composite(left_path: Path, right_path: Path, output_path: Path, phase: str) -> None:
    left = Image.open(left_path).convert("RGB")
    right = Image.open(right_path).convert("RGB")
    header_h = 34
    gap = 10
    canvas = Image.new("RGB", (left.width + right.width + gap, max(left.height, right.height) + header_h), (7, 9, 14))
    canvas.paste(left, (0, header_h))
    canvas.paste(right, (left.width + gap, header_h))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    draw.text((12, 8), "Mines :3000 reference", fill=(245, 248, 255), font=font)
    draw.text((left.width + gap + 12, 8), f"BOXE :3100 {phase}", fill=(245, 248, 255), font=font)
    draw.line((left.width + gap // 2, 0, left.width + gap // 2, canvas.height), fill=(255, 255, 255))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["pre", "post"])
    parser.add_argument("--mines-url", default="http://localhost:3000/mines?title_code=mines_classic&mode=demo&embed=1")
    parser.add_argument("--boxe-url", default="http://localhost:3100/boxe?title_code=boxe001&mode=demo&embed=1")
    parser.add_argument("--executable-path", default=None)
    args = parser.parse_args()

    raw_dir = ARTIFACT_DIR / f"{args.phase}_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = launch_chromium(playwright, args.executable_path)
        outputs: list[Path] = []
        for name, width, height, target_state in STATES:
            print(f"capturing {args.phase} {name} {width}x{height} {target_state}")
            mines = capture_single(browser, "mines", args.mines_url, name, width, height, target_state, raw_dir)
            boxe = capture_single(browser, "boxe", args.boxe_url, name, width, height, target_state, raw_dir)
            output = ARTIFACT_DIR / f"{args.phase}_side_by_side_{name}.png"
            composite(mines, boxe, output, args.phase)
            outputs.append(output)
        browser.close()

    print("\\n".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()
