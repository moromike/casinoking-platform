#!/usr/bin/env python3
"""
GMP-5C B5 — BOXE Runtime Launch-Token Network Verification
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000/api/v1"
DATABASE_URL = "postgresql://casinoking:casinoking@localhost:56543/casinoking"


def _create_player() -> dict[str, str]:
    email = f"gmp5c-{uuid4().hex[:12]}@example.com"
    password = f"StrongPass-{uuid4().hex[:12]}"
    response = httpx.post(
        f"{BACKEND_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "site_access_password": "change-me",
            "first_name": "GMP5C",
            "last_name": "Test",
            "fiscal_code": f"FC{uuid4().hex[:14]}"[:16].upper(),
            "phone_number": f"+39{uuid4().int % 10**10:010d}",
        },
    )
    if response.status_code == 409:
        # Already exists, login directly
        pass
    else:
        response.raise_for_status()

    login_resp = httpx.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password},
    )
    login_resp.raise_for_status()
    data = login_resp.json()["data"]
    return {
        "email": email,
        "password": password,
        "access_token": data["access_token"],
        "user_id": data["user_id"],
    }


def _seed_player_storage(page, *, access_token: str, email: str) -> None:
    page.add_init_script(
        f"""
        window.localStorage.setItem('casinoking.access_token', {json.dumps(access_token)});
        window.localStorage.setItem('casinoking.email', {json.dumps(email)});
        window.localStorage.removeItem('casinoking.boxe_current_session_id');
        """
    )


def _run_case(
    case_name: str,
    page_factory,
    *,
    mode: str,
    wallet_source: str | None = None,
    player: dict[str, str] | None = None,
    block_launch_token: bool = False,
) -> tuple[bool, str, dict[str, str] | None]:
    print(f"\n=== CASE: {case_name} ===")
    page = page_factory()

    page.on("console", lambda msg: print(f"  [console {msg.type}] {msg.text}"))
    page.on("pageerror", lambda err: print(f"  [pageerror] {err}"))

    if player:
        _seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
        )

    if block_launch_token:
        def block_launch(route, request):
            if "/games/boxe/launch-token" in request.url:
                print(f"  [BLOCKED] {request.url}")
                route.fulfill(status=500, body='{"detail":"Injected failure"}')
                return
            route.continue_()
        page.route("**/games/boxe/launch-token", block_launch)

    captured_headers: dict[str, str] | None = None

    def handle_route(route, request):
        nonlocal captured_headers
        if request.method == "POST" and "/games/boxe/start" in request.url:
            captured_headers = dict(request.headers)
            print(f"  [CAPTURED] POST {request.url}")
            for k, v in sorted(request.headers.items()):
                if k.lower() in ("authorization", "x-game-launch-token", "idempotency-key"):
                    print(f"    {k}: {v[:60]}...")
        route.continue_()

    page.route("**/games/boxe/start", handle_route)

    query = {"title_code": "boxe001", "mode": mode}
    if wallet_source is not None:
        query["wallet_source"] = wallet_source

    print(f"  Navigating to /runtime/boxe?{urlencode(query)}")
    page.goto(
        f"{FRONTEND_URL}/runtime/boxe?{urlencode(query)}",
        wait_until="domcontentloaded",
        timeout=60000,
    )
    print("  Page loaded (DOMContentLoaded)")

    if mode != "demo":
        print("  Waiting for table balance gate...")
        table_gate = page.get_by_test_id("boxe-table-balance-gate")
        table_gate.wait_for(timeout=15000)
        table_gate.get_by_label("Importo ingresso tavolo").fill("10")
        table_gate.get_by_role("button", name="Entra nel gioco").click()
        print("  Table gate submitted")

    print("  Waiting for boxe-gameplay...")
    page.get_by_test_id("boxe-gameplay").wait_for(timeout=15000)
    print("  Gameplay rendered")

    print("  Skipping provider intro / how-to-play if present...")
    skip = page.locator(".game-provider-bootstrap-skip")
    try:
        skip.wait_for(timeout=5000)
        skip.click()
        print("  Skipped provider intro")
    except Exception as e:
        print(f"  No provider intro skip ({e})")

    cont = page.get_by_role("button", name="Continua")
    try:
        cont.wait_for(timeout=5000)
        cont.click()
        print("  Skipped how-to-play")
    except Exception as e:
        print(f"  No how-to-play continue ({e})")

    # screenshot for debug
    ss_path = f"scripts/gmp5c_{case_name.replace(' ', '_').lower()}.png"
    page.screenshot(path=ss_path)
    print(f"  Screenshot saved to {ss_path}")

    print("  Clicking primary action (Bet)...")
    page.get_by_test_id("boxe-primary-action").click()
    print("  Clicked")

    page.wait_for_timeout(3000)
    page.close()

    if captured_headers is None:
        return False, "Request /games/boxe/start not captured", None

    has_header = "x-game-launch-token" in {k.lower() for k in captured_headers.keys()}
    return has_header, "captured", captured_headers


def main() -> int:
    print("=" * 60)
    print("GMP-5C B5 — BOXE Network Header Verification")
    print("=" * 60)

    player = _create_player()
    print(f"Player: {player['email']}")

    results: list[tuple[str, bool, str]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        def new_page():
            return browser.new_page(viewport={"width": 1365, "height": 768})

        # ---- CASE 1: Demo ----
        has_header, msg, hdrs = _run_case("Demo", new_page, mode="demo")
        if msg == "captured":
            results.append(("Demo", not has_header, "Header ASSENTE" if not has_header else "Header PRESENTE (atteso assente)"))
        else:
            results.append(("Demo", False, msg))

        # ---- CASE 2: Real with token ----
        has_header, msg, hdrs = _run_case("Real with token", new_page, mode="real_cash", wallet_source="real", player=player)
        if msg == "captured":
            results.append(("Real+Token", has_header, "Header PRESENTE" if has_header else "Header ASSENTE (atteso presente)"))
        else:
            results.append(("Real+Token", False, msg))

        # ---- CASE 3: Real fallback (no token + issue fails) ----
        has_header, msg, hdrs = _run_case(
            "Real fallback",
            new_page,
            mode="real_cash",
            wallet_source="real",
            player=player,
            block_launch_token=True,
        )
        if msg == "captured":
            results.append(("Real+Fallback", not has_header, "Header ASSENTE (fallback)" if not has_header else "Header PRESENTE (atteso assente)"))
        else:
            results.append(("Real+Fallback", False, msg))

        browser.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        if not ok:
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
