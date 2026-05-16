from __future__ import annotations

import json
from pathlib import Path
import shutil
import time
from urllib.request import urlopen
from uuid import uuid4

import pytest


playwright = pytest.importorskip("playwright.sync_api")


def _find_chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        "/snap/bin/chromium",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _load_public_mines_config(title_code: str | None = None) -> dict[str, object]:
    suffix = f"?title_code={title_code}" if title_code else ""
    with urlopen(f"http://localhost:8000/api/v1/games/mines/config{suffix}") as response:
        return json.loads(response.read().decode("utf-8"))["data"]


def _publish_browser_mines_config(
    client,
    create_admin_user,
    auth_headers,
    *,
    title_code: str,
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
        "published_locale_code": "en",
    }
    draft_response = client.put(
        f"/admin/games/titles/{title_code}/config",
        headers=auth_headers(admin_user["access_token"]),
        json=payload,
    )
    assert draft_response.status_code == 200, draft_response.text
    publish_response = client.post(
        f"/admin/games/titles/{title_code}/config/publish",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert publish_response.status_code == 200, publish_response.text


def _browser_duplicate_mines_variant(client, auth_headers, *, admin_user: dict[str, object]) -> str:
    title_code = f"mines_browser_cfg_{uuid4().hex[:8]}"
    response = client.post(
        "/admin/games/titles/mines_classic/duplicate",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "title_code": title_code,
            "display_name": "Mines Browser Config Test",
            "site_code": "casinoking",
        },
    )
    assert response.status_code == 200, response.text
    return title_code


def _browser_create_access_session(
    client,
    auth_headers,
    *,
    access_token: str,
    title_code: str | None = None,
) -> str:
    response = client.post(
        "/access-sessions",
        headers=auth_headers(access_token, title_code=title_code),
        json={
            "game_code": "mines",
            **({"title_code": title_code} if title_code else {}),
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _browser_complete_mines_onboarding(page) -> None:
    page.locator(
        ".mines-provider-bootstrap, .mines-how-to-play-overlay, .mines-board, .mines-viewport-guard"
    ).first.wait_for(timeout=15_000)
    if page.locator(".mines-provider-bootstrap").count() > 0:
        page.locator(".mines-provider-bootstrap-skip").wait_for(state="visible", timeout=15_000)
        page.locator(".mines-provider-bootstrap-skip").click()
    if page.locator(".mines-how-to-play-overlay").count() == 0:
        page.locator(".mines-how-to-play-overlay, .mines-board, .mines-viewport-guard").first.wait_for(
            timeout=15_000
        )
    if page.locator(".mines-how-to-play-overlay").count() > 0:
        page.locator(".mines-how-to-play-continue").click()
    page.locator(".mines-board, .mines-viewport-guard, .mines-launch-gate").first.wait_for(
        timeout=15_000
    )


def _browser_seed_player_storage(
    page,
    *,
    access_token: str,
    email: str,
    current_session_id: str | None = None,
    prelude: str = "",
) -> None:
    session_line = (
        "window.localStorage.setItem('casinoking.current_session_id', "
        f"{json.dumps(current_session_id)});"
        if current_session_id is not None
        else "window.localStorage.removeItem('casinoking.current_session_id');"
    )
    page.add_init_script(
        f"""
        {prelude}
        window.localStorage.setItem('casinoking.access_token', {json.dumps(access_token)});
        window.localStorage.setItem('casinoking.email', {json.dumps(email)});
        {session_line}
        """
    )


def _route_mocked_boot_access_session(page, *, title_code: str) -> list[dict[str, object]]:
    requests: list[dict[str, object]] = []

    def handle_access_sessions(route) -> None:
        if route.request.method != "POST":
            route.continue_()
            return
        payload = json.loads(route.request.post_data or "{}")
        requests.append(payload)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "id": f"boot-2a-access-{title_code}",
                        "user_id": "boot-2a-user",
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
    return requests


def _boot_2a_table_session_response(
    *,
    title_code: str,
    access_session_id: str,
    wallet_type: str = "cash",
) -> dict[str, object]:
    return {
        "id": f"boot-2a-table-{title_code}",
        "access_session_id": access_session_id,
        "game_code": "mines",
        "title_code": title_code,
        "site_code": "casinoking",
        "wallet_type": wallet_type,
        "table_budget_amount": "100.000000",
        "table_balance_amount": "95.000000",
        "loss_limit_amount": "100.000000",
        "loss_reserved_amount": "5.000000",
        "loss_consumed_amount": "5.000000",
        "loss_remaining_amount": "95.000000",
        "status": "active",
    }


def _boot_2a_active_session_response(
    *,
    session_id: str,
    wallet_type: str,
    table_session_id: str | None,
) -> dict[str, object]:
    return {
        "game_session_id": session_id,
        "status": "active",
        "grid_size": 25,
        "mine_count": 3,
        "bet_amount": "5.000000",
        "wallet_type": wallet_type,
        "table_session_id": table_session_id,
        "safe_reveals_count": 0,
        "revealed_cells": [],
        "multiplier_current": "1.00",
        "potential_payout": "0.000000",
        "wallet_balance_after_start": "95.000000",
        "fairness_version": "boot-2a",
        "nonce": 1,
        "server_seed_hash": "0" * 64,
        "board_hash": "0" * 64,
        "ledger_transaction_id": "",
        "created_at": "2026-05-15T00:00:00+00:00",
        "closed_at": None,
    }


def _route_mocked_boot_theme(
    page,
    *,
    title_code: str,
    delay_seconds: float = 0,
    assets: dict[str, str] | None = None,
) -> list[str]:
    requests: list[str] = []

    def handle_theme(route) -> None:
        requests.append(route.request.url)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "title_code": title_code,
                        "tokens": {},
                        "assets": assets or {},
                        "skin": None,
                        "etag": "boot-2a-theme",
                    },
                }
            ),
        )

    page.route(f"**/api/v1/titles/{title_code}/theme", handle_theme)
    return requests


def _route_failed_boot_config(page) -> list[str]:
    requests: list[str] = []

    def handle_config(route) -> None:
        requests.append(route.request.url)
        route.fulfill(
            status=500,
            content_type="application/json",
            body=json.dumps({"success": False, "error": {"message": "BOOT-2A config failure"}}),
        )

    page.route("**/api/v1/games/mines/config?*", handle_config)
    return requests


def _route_mocked_boot_config(
    page,
    *,
    title_code: str,
    runtime_config: dict[str, object],
    delay_seconds: float = 0,
) -> list[str]:
    requests: list[str] = []

    def handle_config(route) -> None:
        requests.append(route.request.url)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"success": True, "data": runtime_config}),
        )

    page.route("**/api/v1/games/mines/config?*", handle_config)
    return requests


def _install_mock_audio(page) -> None:
    page.add_init_script(
        """
        window.__ckAudioPlayCalls = 0;
        window.__ckAudioCreated = 0;
        window.__ckAudioPlaySources = [];

        class CKMockAudio {
            constructor(src) {
                this.src = src;
                this.preload = "";
                this.volume = 1;
                this.currentTime = 0;
                window.__ckAudioCreated += 1;
            }
            play() {
                window.__ckAudioPlayCalls += 1;
                window.__ckAudioPlaySources.push(this.src);
                return Promise.resolve();
            }
            pause() {}
            load() {}
            removeAttribute() {}
        }

        window.Audio = CKMockAudio;
        """
    )


def _browser_lose_round(
    client,
    auth_headers,
    db_helpers,
    *,
    access_token: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    access_session_id: str,
    title_code: str | None = None,
) -> str:
    response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(access_token, title_code=title_code),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert response.status_code == 200, response.text
    session_id = response.json()["data"]["game_session_id"]
    mine_cell = db_helpers.get_mine_positions(session_id)[0]
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(access_token),
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text
    return session_id


def _browser_start_round(
    client,
    auth_headers,
    *,
    access_token: str,
    idempotency_key: str,
    grid_size: int,
    mine_count: int,
    access_session_id: str,
) -> str:
    response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(access_token),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "grid_size": grid_size,
            "mine_count": mine_count,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["game_session_id"]


@pytest.mark.integration
def test_boot_missing_title_redirects_home(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.goto(f"{frontend_base_url}/mines?mode=demo&embed=1", wait_until="domcontentloaded")
        page.wait_for_url(frontend_base_url + "/", timeout=15_000)
        browser.close()


@pytest.mark.integration
def test_boot_real_mode_balance_gate_blocks_intro(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="boot-2a-real-gate-player")
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_real_gate_{uuid4().hex[:8]}",
            display_name="BOOT 2A Real Gate Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _browser_seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
        )
        access_session_requests = _route_mocked_boot_access_session(page, title_code=title_code)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&wallet_source=real&embed=1",
            wait_until="networkidle",
        )

        page.locator(".mines-launch-gate").wait_for(state="visible", timeout=15_000)
        assert page.locator(".mines-provider-bootstrap").count() == 0
        assert page.locator(".mines-how-to-play-overlay").count() == 0
        assert access_session_requests

        browser.close()


@pytest.mark.integration
def test_boot_stores_real_launch_token_storage_keys(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="boot-2a-real-storage-player")
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_real_storage_{uuid4().hex[:8]}",
            display_name="BOOT 2A Real Storage Test",
        )["title_code"]
    )
    access_session_id = f"boot-2a-access-{title_code}"
    table_session = _boot_2a_table_session_response(
        title_code=title_code,
        access_session_id=access_session_id,
    )
    real_launch_requests: list[dict[str, object]] = []
    start_requests: list[dict[str, object]] = []

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _browser_seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
            prelude="window.localStorage.setItem('casinoking.mines_table_session_id', 'legacy-table-session');",
        )
        _route_mocked_boot_access_session(page, title_code=title_code)

        def handle_table_session(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "data": table_session}),
            )

        def handle_launch_token(route) -> None:
            real_launch_requests.append(json.loads(route.request.post_data or "{}"))
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_code": "mines",
                            "title_code": title_code,
                            "game_launch_token": "boot-2a-real-launch-token",
                            "platform_session_id": "boot-2a-platform-session",
                            "play_session_id": "boot-2a-play-session",
                            "game_play_session_id": "boot-2a-game-play-session",
                            "expires_at": "2099-01-01T00:00:00+00:00",
                        },
                    }
                ),
            )

        def handle_validate(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_code": "mines",
                            "title_code": title_code,
                            "player_id": str(player["user_id"]),
                            "platform_session_id": "boot-2a-platform-session",
                            "play_session_id": "boot-2a-play-session",
                            "game_play_session_id": "boot-2a-game-play-session",
                            "expires_at": "2099-01-01T00:00:00+00:00",
                        },
                    }
                ),
            )

        def handle_start(route) -> None:
            start_requests.append(
                {
                    "payload": json.loads(route.request.post_data or "{}"),
                    "launchToken": route.request.headers.get("x-game-launch-token"),
                }
            )
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_session_id": "boot-2a-real-storage-session",
                            "table_session_id": table_session["id"],
                            "table_session": table_session,
                        },
                    }
                ),
            )

        def handle_session(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": _boot_2a_active_session_response(
                            session_id="boot-2a-real-storage-session",
                            wallet_type="cash",
                            table_session_id=str(table_session["id"]),
                        ),
                    }
                ),
            )

        page.route("**/api/v1/table-sessions", handle_table_session)
        page.route("**/api/v1/games/mines/launch-token", handle_launch_token)
        page.route("**/api/v1/games/mines/launch/validate", handle_validate)
        page.route("**/api/v1/games/mines/start", handle_start)
        page.route("**/api/v1/games/mines/session/boot-2a-real-storage-session", handle_session)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&wallet_source=real&embed=1",
            wait_until="networkidle",
        )
        page.locator(".mines-launch-gate").wait_for(state="visible", timeout=15_000)
        assert page.evaluate("() => window.localStorage.getItem('casinoking.mines_table_session_id')") is None
        page.locator(".mines-launch-gate button[type='submit']").click()
        _browser_complete_mines_onboarding(page)
        page.locator(".mines-action-buttons button[type='submit']").click()
        page.wait_for_function(
            "() => window.localStorage.getItem('casinoking.mines_launch_token') === 'boot-2a-real-launch-token'"
        )

        storage_state = page.evaluate(
            f"""
            () => ({{
                token: window.localStorage.getItem('casinoking.mines_launch_token'),
                expiresAt: window.localStorage.getItem('casinoking.mines_launch_token_expires_at'),
                titleCode: window.localStorage.getItem('casinoking.mines_launch_title_code'),
            }})
            """
        )
        assert storage_state == {
            "token": "boot-2a-real-launch-token",
            "expiresAt": "2099-01-01T00:00:00+00:00",
            "titleCode": title_code,
        }
        assert real_launch_requests == [{"game_code": "mines", "title_code": title_code}]
        assert start_requests
        assert start_requests[-1]["launchToken"] == "boot-2a-real-launch-token"

        browser.close()


@pytest.mark.integration
def test_boot_preserves_pre_refactor_demo_storage_keys(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_storage_{uuid4().hex[:8]}",
            display_name="BOOT 2A Storage Compatibility Test",
        )["title_code"]
    )
    start_requests: list[dict[str, object]] = []
    demo_launch_requests: list[dict[str, object]] = []

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        page.add_init_script(
            f"""
            window.localStorage.setItem('casinoking.mines_table_session_id', 'legacy-table-session');
            window.localStorage.setItem('ck_demo_anon_token', 'pre-refactor-anon');
            window.localStorage.setItem('ck_demo_game_launch_token', 'pre-refactor-demo-launch');
            window.localStorage.setItem('ck_demo_game_launch_token_expires_at', '2099-01-01T00:00:00+00:00');
            window.localStorage.setItem('ck_demo_game_launch_title_code', {json.dumps(title_code)});
            window.localStorage.setItem('ck_demo_chip_balance', '77.000000');
            """
        )

        def reject_demo_launch(route) -> None:
            demo_launch_requests.append(json.loads(route.request.post_data or "{}"))
            route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": False,
                        "error": {
                            "code": "UNEXPECTED_DEMO_LAUNCH",
                            "message": "Stored demo launch token should have been reused.",
                        },
                    }
                ),
            )

        def handle_start(route) -> None:
            start_requests.append(
                {
                    "payload": json.loads(route.request.post_data or "{}"),
                    "launchToken": route.request.headers.get("x-game-launch-token"),
                }
            )
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_session_id": "boot-2a-storage-session",
                            "wallet_balance_after": "72.000000",
                        },
                    }
                ),
            )

        def handle_session(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_session_id": "boot-2a-storage-session",
                            "status": "active",
                            "grid_size": 25,
                            "mine_count": 3,
                            "bet_amount": "5.000000",
                            "wallet_type": "demo",
                            "table_session_id": None,
                            "safe_reveals_count": 0,
                            "revealed_cells": [],
                            "multiplier_current": "1.00",
                            "potential_payout": "0.000000",
                            "wallet_balance_after_start": "72.000000",
                            "fairness_version": "boot-2a",
                            "nonce": 1,
                            "server_seed_hash": "0" * 64,
                            "board_hash": "0" * 64,
                            "ledger_transaction_id": "",
                            "created_at": "2026-05-15T00:00:00+00:00",
                            "closed_at": None,
                        },
                    }
                ),
            )

        page.route("**/api/v1/demo/launch", reject_demo_launch)
        page.route("**/api/v1/games/mines/start", handle_start)
        page.route("**/api/v1/games/mines/session/boot-2a-storage-session", handle_session)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        assert page.evaluate("() => window.localStorage.getItem('casinoking.mines_table_session_id')") is None
        _browser_complete_mines_onboarding(page)
        page.locator(".mines-action-buttons button[type='submit']").click()
        page.wait_for_function("() => document.querySelectorAll('.board-cell:not(:disabled)').length > 0")

        assert demo_launch_requests == []
        assert start_requests
        assert start_requests[-1]["launchToken"] == "pre-refactor-demo-launch"
        assert page.evaluate("() => window.localStorage.getItem('ck_demo_chip_balance')") == "72.000000"

        browser.close()


@pytest.mark.integration
def test_boot_title_mismatch_clears_token(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_title_match_{uuid4().hex[:8]}",
            display_name="BOOT 2A Title Match Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.add_init_script(
            """
            window.localStorage.setItem('casinoking.mines_launch_token', 'wrong-real-token');
            window.localStorage.setItem('casinoking.mines_launch_token_expires_at', '2099-01-01T00:00:00+00:00');
            window.localStorage.setItem('casinoking.mines_launch_title_code', 'other_title');
            window.localStorage.setItem('ck_demo_anon_token', 'demo-anon-token');
            window.localStorage.setItem('ck_demo_game_launch_token', 'wrong-demo-token');
            window.localStorage.setItem('ck_demo_game_launch_token_expires_at', '2099-01-01T00:00:00+00:00');
            window.localStorage.setItem('ck_demo_game_launch_title_code', 'other_title');
            """
        )
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )

        storage_state = page.evaluate(
            """
            () => ({
                realToken: window.localStorage.getItem('casinoking.mines_launch_token'),
                realTokenExpires: window.localStorage.getItem('casinoking.mines_launch_token_expires_at'),
                realTokenTitle: window.localStorage.getItem('casinoking.mines_launch_title_code'),
                demoToken: window.localStorage.getItem('ck_demo_game_launch_token'),
                demoTokenExpires: window.localStorage.getItem('ck_demo_game_launch_token_expires_at'),
                demoTokenTitle: window.localStorage.getItem('ck_demo_game_launch_title_code'),
            })
            """
        )
        assert storage_state == {
            "realToken": None,
            "realTokenExpires": None,
            "realTokenTitle": None,
            "demoToken": None,
            "demoTokenExpires": None,
            "demoTokenTitle": None,
        }

        browser.close()

        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.add_init_script(
            """
            window.localStorage.setItem('ck_demo_game_launch_token', 'wrong-demo-token-without-anon');
            window.localStorage.setItem('ck_demo_game_launch_token_expires_at', '2099-01-01T00:00:00+00:00');
            window.localStorage.setItem('ck_demo_game_launch_title_code', 'other_title');
            """
        )
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )

        storage_state = page.evaluate(
            """
            () => ({
                demoToken: window.localStorage.getItem('ck_demo_game_launch_token'),
                demoTokenExpires: window.localStorage.getItem('ck_demo_game_launch_token_expires_at'),
                demoTokenTitle: window.localStorage.getItem('ck_demo_game_launch_title_code'),
            })
            """
        )
        assert storage_state == {
            "demoToken": None,
            "demoTokenExpires": None,
            "demoTokenTitle": None,
        }

        browser.close()

        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.add_init_script(
            f"""
            window.localStorage.setItem('ck_demo_game_launch_token', 'right-title-token-without-anon');
            window.localStorage.setItem('ck_demo_game_launch_token_expires_at', '2099-01-01T00:00:00+00:00');
            window.localStorage.setItem('ck_demo_game_launch_title_code', {json.dumps(title_code)});
            """
        )
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )

        storage_state = page.evaluate(
            """
            () => ({
                demoToken: window.localStorage.getItem('ck_demo_game_launch_token'),
                demoTokenExpires: window.localStorage.getItem('ck_demo_game_launch_token_expires_at'),
                demoTokenTitle: window.localStorage.getItem('ck_demo_game_launch_title_code'),
            })
            """
        )
        assert storage_state == {
            "demoToken": None,
            "demoTokenExpires": None,
            "demoTokenTitle": None,
        }

        browser.close()


@pytest.mark.integration
def test_boot_preview_token_loads_demo_without_publish(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = f"boot_2a_preview_{uuid4().hex[:8]}"
    runtime_config = _load_public_mines_config("mines_classic")
    demo_launch_requests: list[dict[str, object]] = []

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        _route_mocked_boot_config(page, title_code=title_code, runtime_config=runtime_config)
        _route_mocked_boot_theme(page, title_code=title_code)

        def handle_demo_token(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True, "data": {"anonymous_token": "boot-2a-anon"}}),
            )

        def handle_demo_launch(route) -> None:
            payload = json.loads(route.request.post_data or "{}")
            demo_launch_requests.append(payload)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": {
                            "game_launch_token": "boot-2a-demo-launch-token",
                            "expires_at": "2099-01-01T00:00:00+00:00",
                            "balance_chips": "100.000000",
                        },
                    }
                ),
            )

        page.route("**/api/v1/demo/token", handle_demo_token)
        page.route("**/api/v1/demo/launch", handle_demo_launch)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&preview=1&preview_token=preview-token-123&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.locator(".mines-action-buttons button[type='submit']").click()
        page.wait_for_function("() => window.localStorage.getItem('ck_demo_game_launch_token') !== null")

        assert demo_launch_requests
        assert demo_launch_requests[-1]["title_code"] == title_code
        assert demo_launch_requests[-1]["preview_token"] == "preview-token-123"
        assert page.locator(".mines-launch-gate").count() == 0

        browser.close()


@pytest.mark.integration
def test_boot_embed_param_no_overflow(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_embed_{uuid4().hex[:8]}",
            display_name="BOOT 2A Embed Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 375, "height": 812})
        page.emulate_media(reduced_motion="reduce")
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        metrics = page.evaluate(
            """
            () => ({
                horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                verticalOverflow: document.documentElement.scrollHeight > window.innerHeight + 1,
                embedded: Boolean(document.querySelector('.mines-page-shell-embedded')),
                boardVisible: Boolean(document.querySelector('.mines-board')),
            })
            """
        )
        assert metrics == {
            "horizontalOverflow": False,
            "verticalOverflow": False,
            "embedded": True,
            "boardVisible": True,
        }

        browser.close()


@pytest.mark.integration
def test_boot_rules_modal_fits_shell_and_uses_body_scroll(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_rules_modal_{uuid4().hex[:8]}",
            display_name="BOOT Rules Modal Fit Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 928, "height": 725})
        page.emulate_media(reduced_motion="reduce")
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.locator(".mines-rules-trigger").click()
        page.locator(".mines-rules-modal").wait_for(timeout=10_000)

        metrics = page.evaluate(
            """
            () => {
                const rect = (node) => {
                    const box = node.getBoundingClientRect();
                    return {
                        left: box.left,
                        top: box.top,
                        right: box.right,
                        bottom: box.bottom,
                        width: box.width,
                        height: box.height,
                    };
                };
                const shell = document.querySelector('.mines-product-shell');
                const modal = document.querySelector('.mines-rules-modal');
                const body = document.querySelector('.mines-rules-body');
                const payoutRows = Array.from(
                    document.querySelectorAll('.mines-rules-modal .payout-ladder-row')
                );
                const bodyBox = rect(body);
                return {
                    modalInsideShell:
                        modal.getBoundingClientRect().left >= shell.getBoundingClientRect().left - 1 &&
                        modal.getBoundingClientRect().right <= shell.getBoundingClientRect().right + 1 &&
                        modal.getBoundingClientRect().top >= shell.getBoundingClientRect().top - 1 &&
                        modal.getBoundingClientRect().bottom <= shell.getBoundingClientRect().bottom + 1,
                    bodyClientHeight: body.clientHeight,
                    bodyScrollHeight: body.scrollHeight,
                    visiblePayoutRows: payoutRows.filter((row) => rect(row).bottom <= bodyBox.bottom).length,
                    closeBackground: getComputedStyle(document.querySelector('.mines-rules-close')).backgroundColor,
                };
            }
            """
        )

        assert metrics["modalInsideShell"] is True
        assert metrics["bodyClientHeight"] > 0
        assert metrics["bodyScrollHeight"] >= metrics["bodyClientHeight"]
        assert metrics["visiblePayoutRows"] >= 8
        assert metrics["closeBackground"] == "rgba(0, 0, 0, 0)"

        browser.close()


@pytest.mark.integration
def test_boot_wallet_source_query_param_hint(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="boot-2a-wallet-source-player")
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_wallet_{uuid4().hex[:8]}",
            display_name="BOOT 2A Wallet Source Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _browser_seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
        )
        _route_mocked_boot_access_session(page, title_code=title_code)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&wallet_source=bonus&embed=1",
            wait_until="networkidle",
        )

        summary = page.locator(".mines-launch-source-summary")
        summary.wait_for(state="visible", timeout=15_000)
        assert "bonus" in summary.inner_text().lower()
        assert page.locator(".mines-wallet-choice").count() == 0

        browser.close()


@pytest.mark.integration
def test_boot_wallet_source_real_query_param_hint(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="boot-2a-wallet-source-real-player")
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_wallet_real_{uuid4().hex[:8]}",
            display_name="BOOT 2A Wallet Source Real Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _browser_seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
        )
        _route_mocked_boot_access_session(page, title_code=title_code)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&wallet_source=real&embed=1",
            wait_until="networkidle",
        )

        summary = page.locator(".mines-launch-source-summary")
        summary.wait_for(state="visible", timeout=15_000)
        assert "real" in summary.inner_text().lower()
        assert page.locator(".mines-wallet-choice").count() == 0

        browser.close()


@pytest.mark.integration
def test_boot_intro_progress_bar_tied_to_runtime_ready(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_intro_{uuid4().hex[:8]}",
            display_name="BOOT 2A Intro Readiness Test",
        )["title_code"]
    )
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        config_requests: list[str] = []

        def hold_config(route) -> None:
            config_requests.append(route.request.url)

        page.route("**/api/v1/games/mines/config?*", hold_config)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="domcontentloaded",
        )
        page.locator(".mines-provider-bootstrap").wait_for(state="visible", timeout=2_000)
        page.wait_for_function("() => document.querySelector('.mines-provider-bootstrap-skip') === null")
        assert page.locator(".mines-provider-bootstrap-skip").count() == 0
        assert config_requests

        browser.close()


@pytest.mark.integration
def test_boot_does_not_mount_gameplay_until_runtime_ready(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_ready_{uuid4().hex[:8]}",
            display_name="BOOT 2A Runtime Ready Test",
        )["title_code"]
    )
    runtime_config = _load_public_mines_config("mines_classic")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        config_requests: list[str] = []
        theme_requests: list[str] = []
        held_config_route = {}
        held_theme_route = {}

        def hold_config(route) -> None:
            config_requests.append(route.request.url)
            held_config_route["route"] = route

        def hold_theme(route) -> None:
            theme_requests.append(route.request.url)
            held_theme_route["route"] = route

        page.route("**/api/v1/games/mines/config?*", hold_config)
        page.route(f"**/api/v1/titles/{title_code}/theme", hold_theme)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="domcontentloaded",
        )

        page.locator("main[data-game-boot-status='launch_ready']").wait_for(
            state="attached",
            timeout=5_000,
        )
        page.locator(".mines-provider-bootstrap").wait_for(state="visible", timeout=5_000)
        assert page.locator("main[data-game-boot-status='launch_ready']").count() == 1
        for _ in range(50):
            if held_config_route and held_theme_route:
                break
            page.wait_for_timeout(100)
        assert config_requests
        assert theme_requests
        assert page.locator(".mines-stage-board").count() == 0
        assert page.locator(".mines-action-buttons").count() == 0
        assert page.locator(".mines-how-to-play-overlay").count() == 0

        held_theme_route["route"].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "title_code": title_code,
                        "tokens": {},
                        "assets": {},
                        "skin": None,
                        "etag": "boot-2a-theme",
                    },
                }
            ),
        )
        held_config_route["route"].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"success": True, "data": runtime_config}),
        )
        page.locator("main[data-game-boot-status='runtime_ready']").wait_for(
            state="attached",
            timeout=15_000,
        )
        page.locator(".mines-provider-bootstrap-skip").wait_for(state="visible", timeout=10_000)

        browser.close()


@pytest.mark.integration
def test_boot_config_failure_sets_fatal_status(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_fatal_{uuid4().hex[:8]}",
            display_name="BOOT 2A Fatal Runtime Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        config_requests = _route_failed_boot_config(page)
        _route_mocked_boot_theme(page, title_code=title_code)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="domcontentloaded",
        )

        page.locator("main[data-game-boot-status='fatal']").wait_for(
            state="attached",
            timeout=15_000,
        )
        page.locator(".mines-error-dialog").wait_for(state="visible", timeout=15_000)
        assert page.locator(".mines-stage-board").count() == 0
        assert page.locator(".mines-action-buttons").count() == 0
        assert config_requests

        browser.close()


@pytest.mark.integration
def test_boot_audio_preferences_read_existing_platform_keys(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_audio_read_{uuid4().hex[:8]}",
            display_name="BOOT 2A Audio Read Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        page.add_init_script(
            """
            window.localStorage.setItem('ck.audio.effectsMuted', 'true');
            window.localStorage.setItem('ck.audio.effectsVolume', '0.25');
            """
        )
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)

        page.locator(".mines-audio-trigger.is-muted").wait_for(state="visible", timeout=15_000)
        page.locator(".mines-audio-trigger").click()
        assert page.locator(".mines-audio-volume input").input_value() == "25"

        browser.close()


@pytest.mark.integration
def test_boot_audio_mute_ui_persists_platform_key(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_audio_write_{uuid4().hex[:8]}",
            display_name="BOOT 2A Audio Write Test",
        )["title_code"]
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        page.add_init_script(
            """
            window.localStorage.removeItem('ck.audio.effectsMuted');
            window.localStorage.removeItem('ck.audio.effectsVolume');
            """
        )
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)

        page.locator(".mines-audio-trigger").wait_for(state="visible", timeout=15_000)
        page.locator(".mines-audio-trigger").click()
        page.locator(".mines-audio-toggle").click()
        page.wait_for_function(
            "() => window.localStorage.getItem('ck.audio.effectsMuted') === 'true'",
            timeout=5_000,
        )
        assert page.evaluate("() => window.localStorage.getItem('ck.audio.effectsMuted')") == "true"

        browser.close()


@pytest.mark.integration
def test_boot_audio_mute_reaches_gameplay_sound_events(
    frontend_base_url: str,
    wait_for_frontend,
    create_published_mines_variant,
) -> None:
    del wait_for_frontend
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_audio_gameplay_{uuid4().hex[:8]}",
            display_name="BOOT 2A Audio Gameplay Test",
        )["title_code"]
    )
    audio_assets = {
        "audio_safe_reveal": "/static/test/audio-safe.mp3",
        "audio_mine_hit": "/static/test/audio-mine.mp3",
        "audio_collect": "/static/test/audio-collect.mp3",
        "audio_win": "/static/test/audio-win.mp3",
    }

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        _install_mock_audio(page)
        _route_mocked_boot_theme(page, title_code=title_code, assets=audio_assets)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.wait_for_function("() => window.__ckAudioCreated >= 4", timeout=15_000)

        page.locator(".mines-audio-trigger").click()
        page.locator(".mines-audio-toggle").click()
        page.wait_for_function(
            "() => window.localStorage.getItem('ck.audio.effectsMuted') === 'true'",
            timeout=5_000,
        )
        page.locator(".mines-action-buttons button[type='submit']").click()
        page.locator(".board-cell:not([disabled])").first.wait_for(
            state="visible",
            timeout=15_000,
        )
        page.locator(".board-cell:not([disabled])").first.click()
        page.wait_for_timeout(500)

        assert page.evaluate("() => window.__ckAudioPlayCalls") == 0

        browser.close()


@pytest.mark.integration
def test_boot_bet_does_not_flash_previous_safe_reveal(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend
    title_code = str(
        create_published_mines_variant(
            title_code=f"boot_2a_no_flash_{uuid4().hex[:8]}",
            display_name="BOOT 2A No Flash Test",
        )["title_code"]
    )
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        title_code=title_code,
        published_grid_sizes=[25],
        published_mine_counts={"25": [1]},
        default_mine_counts={"25": 1},
    )

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    next_session_id = "boot-2a-no-flash-next-session"
    pending_start_routes = []

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        page.emulate_media(reduced_motion="reduce")
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.get_by_role("button", name="5x5").click()
        page.locator(".field").nth(1).locator("button.choice-chip").filter(has_text="1").first.click()

        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url
            and response.request.method == "POST"
        ) as start_response_info:
            page.get_by_role("button", name="Bet").click()
        session_id = start_response_info.value.json()["data"]["game_session_id"]
        mine_positions_row = db_helpers.fetchone(
            "SELECT mine_positions_json FROM demo_mines_game_rounds WHERE id = %s",
            (session_id,),
        )
        assert mine_positions_row is not None
        mine_positions = set(mine_positions_row["mine_positions_json"])
        safe_cell = next(index for index in range(25) if index not in mine_positions)

        page.wait_for_function("() => document.querySelectorAll('.board-cell:not(:disabled)').length > 0")
        page.locator(".board-cell").nth(safe_cell).click()
        page.locator(".board-cell.revealed-safe").wait_for(state="visible", timeout=5_000)
        page.wait_for_function(
            """
            () => Array.from(document.querySelectorAll('button')).some(
                (button) => button.textContent?.trim() === 'Collect' && !button.disabled
            )
            """,
            timeout=15_000,
        )

        with page.expect_response(
            lambda response: "/api/v1/games/mines/cashout" in response.url
            and response.request.method == "POST"
        ):
            page.get_by_role("button", name="Collect").click()
        page.locator(".board-cell.revealed-safe").wait_for(state="visible", timeout=5_000)

        def hold_next_start(route) -> None:
            if route.request.method != "POST":
                route.continue_()
                return
            pending_start_routes.append(route)

        def handle_next_session(route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": True,
                        "data": _boot_2a_active_session_response(
                            session_id=next_session_id,
                            wallet_type="demo",
                            table_session_id=None,
                        ),
                    }
                ),
            )

        page.route("**/api/v1/games/mines/start", hold_next_start)
        page.route(f"**/api/v1/games/mines/session/{next_session_id}", handle_next_session)

        with page.expect_request(
            lambda request: "/api/v1/games/mines/start" in request.url
            and request.method == "POST"
        ):
            page.get_by_role("button", name="Bet").click()
        page.wait_for_timeout(250)

        assert len(pending_start_routes) == 1
        during_loading_metrics = page.evaluate(
            """
            () => ({
                revealedSafe: document.querySelectorAll('.board-cell.revealed-safe').length,
                safeState: document.querySelectorAll('.board-cell[data-board-state="safe"]').length,
                safeSymbols: document.querySelectorAll(
                    '.board-cell.revealed-safe .board-cell-face-visual svg, ' +
                    '.board-cell.revealed-safe .board-cell-face-visual img'
                ).length,
                mineState: document.querySelectorAll('.board-cell[data-board-state="mine"]').length,
            })
            """
        )

        assert during_loading_metrics == {
            "revealedSafe": 0,
            "safeState": 0,
            "safeSymbols": 0,
            "mineState": 0,
        }

        pending_start_routes[0].fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "success": True,
                    "data": {
                        "game_session_id": next_session_id,
                        "wallet_balance_after": "90.000000",
                    },
                }
            ),
        )
        page.wait_for_function(
            """
            () =>
                document.querySelectorAll('.board-cell:not(:disabled)').length > 0 &&
                document.querySelectorAll('.board-cell.revealed-safe').length === 0 &&
                document.querySelectorAll('.board-cell[data-board-state="mine"]').length === 0
            """,
            timeout=15_000,
        )

        browser.close()


@pytest.mark.integration
def test_mines_embed_uses_selected_runtime_values_and_keeps_footer_visible(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    create_published_mines_variant,
    auth_headers,
) -> None:
    del wait_for_frontend
    title_code = str(
        create_published_mines_variant(
            title_code=f"browser_runtime_values_{uuid4().hex[:8]}",
            display_name="Browser Runtime Values Test",
        )["title_code"]
    )
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        title_code=title_code,
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
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)

        config_sections = page.locator(".mines-config-section")
        mines_field = config_sections.nth(1)
        bet_field = page.locator(".mines-bet-field")

        grid_labels = config_sections.nth(0).locator("button.choice-chip").evaluate_all(
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
            "wallet_type": "demo",
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
        assert footer.locator("strong").count() >= 2

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
        page.goto(f"{frontend_base_url}/mines?title_code=mines_classic&embed=1", wait_until="networkidle")
        _browser_complete_mines_onboarding(page)
        grid_labels = page.locator(".mines-config-section").nth(0).locator("button.choice-chip").evaluate_all(
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
        ("/mines?title_code=mines_classic", 375, 667),
        ("/mines?title_code=mines_classic", 882, 344),
        ("/mines?title_code=mines_classic&embed=1", 375, 667),
        ("/mines?title_code=mines_classic&embed=1", 882, 344),
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
        _browser_complete_mines_onboarding(page)

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
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend
    title_code = str(
        create_published_mines_variant(
            title_code=f"browser_compact_status_{uuid4().hex[:8]}",
            display_name="Browser Compact Status Test",
        )["title_code"]
    )
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        title_code=title_code,
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
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)

        grid_labels = page.locator(".mines-config-section").nth(0).locator("button.choice-chip").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim()).filter(Boolean)"
        )
        target_grid_label = grid_labels[0]
        page.get_by_role("button", name=target_grid_label).click()
        page.locator(".field").nth(1).locator("button.choice-chip").first.click()
        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url
            and response.request.method == "POST"
        ) as start_response_info:
            page.get_by_role("button", name="Bet").click()
        session_id = start_response_info.value.json()["data"]["game_session_id"]
        mine_positions_row = db_helpers.fetchone(
            "SELECT mine_positions_json FROM demo_mines_game_rounds WHERE id = %s",
            (session_id,),
        )
        assert mine_positions_row is not None
        mine_positions = set(mine_positions_row["mine_positions_json"])
        safe_cell = next(index for index in range(25) if index not in mine_positions)
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

        with page.expect_response(
            lambda response: "/api/v1/games/mines/reveal" in response.url
            and response.request.method == "POST"
        ):
            page.locator(".board-cell").nth(safe_cell).click()
        page.wait_for_function(
            "(nextPreview) => document.querySelector('.mines-preview-chip.active')?.textContent?.trim() === nextPreview",
            arg=before["preview"][1],
            timeout=15_000,
        )
        after = page.evaluate(
            """
            () => ({
                preview: Array.from(document.querySelectorAll('.mines-preview-chip')).map(
                    (node) => node.textContent?.trim()
                ),
                activePreview: document.querySelector('.mines-preview-chip.active')?.textContent?.trim(),
                previewCount: document.querySelectorAll('.mines-preview-chip').length,
            })
            """
        )

        assert before["statusCount"] == 0
        assert before["rulesText"] == "i"
        assert before["demoBadge"] in {"DEMO", "DEMO MODE"}
        assert before["innerHomeCount"] == 0
        assert before["stageCloseCount"] == 0
        assert len(before["preview"]) == 5
        assert len(after["preview"]) == 5
        assert before["preview"][1:] == after["preview"][:4]
        assert after["activePreview"] == after["preview"][0]

        browser.close()


@pytest.mark.integration
def test_mines_embed_renders_real_board_symbols_in_dom(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend
    title_code = str(
        create_published_mines_variant(
            title_code=f"browser_board_symbols_{uuid4().hex[:8]}",
            display_name="Browser Board Symbols Test",
        )["title_code"]
    )
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        title_code=title_code,
        published_grid_sizes=[25],
        published_mine_counts={"25": [1]},
        default_mine_counts={"25": 1},
    )

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    audio_assets = {
        "audio_safe_reveal": "/static/test/audio-safe.mp3",
        "audio_mine_hit": "/static/test/audio-mine.mp3",
        "audio_collect": "/static/test/audio-collect.mp3",
        "audio_win": "/static/test/audio-win.mp3",
    }

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.emulate_media(reduced_motion="reduce")
        _install_mock_audio(page)
        _route_mocked_boot_theme(page, title_code=title_code, assets=audio_assets)
        page.goto(f"{frontend_base_url}/mines?title_code={title_code}&embed=1", wait_until="networkidle")
        _browser_complete_mines_onboarding(page)
        page.wait_for_function("() => window.__ckAudioCreated >= 4", timeout=15_000)
        page.get_by_role("button", name="5x5").click()
        page.locator(".field").nth(1).locator("button.choice-chip").filter(has_text="1").first.click()
        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url and response.request.method == "POST"
        ) as start_response_info:
            page.get_by_role("button", name="Bet").click()
        session_id = start_response_info.value.json()["data"]["game_session_id"]
        assert session_id
        mine_positions_row = db_helpers.fetchone(
            "SELECT mine_positions_json FROM demo_mines_game_rounds WHERE id = %s",
            (session_id,),
        )
        assert mine_positions_row is not None
        page.wait_for_timeout(800)
        mine_positions = set(mine_positions_row["mine_positions_json"])
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
        page.locator(".board-cell.effect-safe-reveal").wait_for(state="visible", timeout=1_000)
        assert safe_metrics["safeSymbols"] > 0
        assert safe_metrics["safeCentered"] is not None
        assert safe_metrics["safeCentered"]["xDelta"] <= 6
        assert safe_metrics["safeCentered"]["yDelta"] <= 6
        assert "/static/test/audio-safe.mp3" in page.evaluate("() => window.__ckAudioPlaySources")

        page.locator(".board-cell").nth(mine_cell).click()
        page.wait_for_function(
            """
            () =>
                document.querySelectorAll(
                    '.board-cell.revealed-mine .board-cell-face-visual svg, .board-cell.revealed-mine .board-cell-face-visual img'
                ).length > 0
            """
        )
        page.locator(".board-cell.effect-mine-hit").wait_for(state="visible", timeout=1_000)
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
        session_snapshot = db_helpers.fetchone(
            "SELECT status FROM demo_mines_game_rounds WHERE id = %s",
            (session_id,),
        )
        assert mine_metrics["mineSymbols"] > 0
        assert mine_metrics["mineCentered"] is not None
        assert mine_metrics["mineCentered"]["xDelta"] <= 6
        assert mine_metrics["mineCentered"]["yDelta"] <= 6
        assert "/static/test/audio-mine.mp3" in page.evaluate("() => window.__ckAudioPlaySources")
        assert session_snapshot is not None
        assert session_snapshot["status"] == "lost"
        browser.close()


@pytest.mark.integration
def test_mines_demo_cashout_reveals_mines_and_plays_collect_sound(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend
    title_code = str(
        create_published_mines_variant(
            title_code=f"browser_cashout_{uuid4().hex[:8]}",
            display_name="Browser Cashout Test",
        )["title_code"]
    )
    _publish_browser_mines_config(
        client,
        create_admin_user,
        auth_headers,
        title_code=title_code,
        published_grid_sizes=[25],
        published_mine_counts={"25": [1]},
        default_mine_counts={"25": 1},
    )

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    audio_assets = {
        "audio_safe_reveal": "/static/test/audio-safe.mp3",
        "audio_mine_hit": "/static/test/audio-mine.mp3",
        "audio_collect": "/static/test/audio-collect.mp3",
        "audio_win": "/static/test/audio-win.mp3",
    }
    mine_symbol_selector = (
        ".board-cell.revealed-mine .board-cell-face-visual svg, "
        ".board-cell.revealed-mine .board-cell-face-visual img"
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.emulate_media(reduced_motion="reduce")
        _install_mock_audio(page)
        _route_mocked_boot_theme(page, title_code=title_code, assets=audio_assets)
        page.goto(
            f"{frontend_base_url}/mines?title_code={title_code}&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.wait_for_function("() => window.__ckAudioCreated >= 4", timeout=15_000)
        page.get_by_role("button", name="5x5").click()
        page.locator(".field").nth(1).locator("button.choice-chip").filter(has_text="1").first.click()

        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url
            and response.request.method == "POST"
        ) as start_response_info:
            page.get_by_role("button", name="Bet").click()
        session_id = start_response_info.value.json()["data"]["game_session_id"]
        mine_positions_row = db_helpers.fetchone(
            "SELECT mine_positions_json FROM demo_mines_game_rounds WHERE id = %s",
            (session_id,),
        )
        assert mine_positions_row is not None
        mine_positions = set(mine_positions_row["mine_positions_json"])
        safe_cell = next(index for index in range(25) if index not in mine_positions)

        page.locator(".board-cell").nth(safe_cell).click()
        page.locator(".board-cell.effect-safe-reveal").wait_for(state="visible", timeout=1_000)
        page.wait_for_function(
            """
            () => Array.from(document.querySelectorAll('button')).some(
                (button) => button.textContent?.trim() === 'Collect' && !button.disabled
            )
            """,
            timeout=15_000,
        )

        with page.expect_response(
            lambda response: "/api/v1/games/mines/cashout" in response.url
            and response.request.method == "POST"
        ) as cashout_response_info:
            page.get_by_role("button", name="Collect").click()
        cashout_payload = cashout_response_info.value.json()["data"]
        expected_mine_count = len(cashout_payload["mine_positions"])

        page.wait_for_function(
            """
            ([selector, expectedMineCount]) =>
                document.querySelectorAll(selector).length === expectedMineCount
            """,
            arg=[mine_symbol_selector, expected_mine_count],
            timeout=5_000,
        )
        page.locator(".mines-win-celebration").wait_for(state="visible", timeout=5_000)
        played_sources = page.evaluate("() => window.__ckAudioPlaySources")

        assert expected_mine_count == 1
        assert page.locator(mine_symbol_selector).count() == expected_mine_count
        assert "/static/test/audio-safe.mp3" in played_sources
        assert "/static/test/audio-collect.mp3" in played_sources
        assert "/static/test/audio-win.mp3" not in played_sources
        browser.close()


@pytest.mark.integration
def test_mines_demo_loss_reveals_all_mines_before_session_refresh(
    frontend_base_url: str,
    wait_for_frontend,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    mine_symbol_selector = (
        ".board-cell.revealed-mine .board-cell-face-visual svg, "
        ".board-cell.revealed-mine .board-cell-face-visual img"
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1463, "height": 735})
        page.goto(
            f"{frontend_base_url}/mines?title_code=mines001b&mode=demo&embed=1",
            wait_until="networkidle",
        )
        _browser_complete_mines_onboarding(page)
        page.get_by_role("button", name="5x5").click()
        mine_option_buttons = page.locator(".field").nth(1).locator("button.choice-chip")
        mine_option_labels = mine_option_buttons.evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )
        mine_counts = [
            int(label)
            for label in mine_option_labels
            if label.isdigit()
        ]
        assert mine_counts
        target_mine_count = max(mine_counts)
        page.locator(".field").nth(1).locator("button.choice-chip").nth(
            mine_option_labels.index(str(target_mine_count))
        ).click()

        with page.expect_response(
            lambda response: "/api/v1/games/mines/start" in response.url
            and response.request.method == "POST"
        ):
            page.get_by_role("button", name="Bet").click()
        page.wait_for_function(
            "() => document.querySelectorAll('.board-cell:not(:disabled)').length > 0"
        )

        def delay_session_refresh(route) -> None:
            if "/api/v1/games/mines/session/" in route.request.url:
                time.sleep(1)
            route.continue_()

        page.route("**/api/v1/games/mines/session/*", delay_session_refresh)
        loss_seen = False
        for cell_index in range(25):
            cell = page.locator(".board-cell").nth(cell_index)
            if not cell.is_enabled():
                continue

            with page.expect_response(
                lambda response: "/api/v1/games/mines/reveal" in response.url
                and response.request.method == "POST"
            ) as reveal_response_info:
                cell.click()
            reveal_payload = reveal_response_info.value.json()["data"]
            if reveal_payload["result"] != "mine":
                page.wait_for_function(
                    """
                    () => Array.from(document.querySelectorAll('.board-cell')).some(
                        (cell) => !cell.disabled && cell.getAttribute('data-board-state') === 'hidden'
                    )
                    """
                )
                continue

            loss_seen = True
            expected_mine_count = len(reveal_payload["mine_positions"])
            assert expected_mine_count == target_mine_count
            page.wait_for_function(
                """
                ([selector, expectedMineCount]) =>
                    document.querySelectorAll(selector).length === expectedMineCount
                """,
                arg=[mine_symbol_selector, expected_mine_count],
                timeout=500,
            )
            assert page.locator(mine_symbol_selector).count() == expected_mine_count
            break

        assert loss_seen
        browser.close()


@pytest.mark.integration
def test_mines_resume_prefers_active_game_session_over_stored_access_session_id(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="browser-mines-resume-player")
    access_session_id = _browser_create_access_session(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
    )
    active_game_session_id = _browser_start_round(
        client,
        auth_headers,
        access_token=str(player["access_token"]),
        idempotency_key="browser-mines-resume-active-round",
        grid_size=25,
        mine_count=3,
        access_session_id=access_session_id,
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})

        page.add_init_script(
            f"""
            () => {{
                window.localStorage.setItem('casinoking.access_token', {json.dumps(str(player['access_token']))});
                window.localStorage.setItem('casinoking.email', {json.dumps(str(player['email']))});
                window.localStorage.setItem('casinoking.current_session_id', {json.dumps(access_session_id)});
            }}
            """
        )

        def delay_session_resume(route) -> None:
            if f"/api/v1/games/mines/session/{active_game_session_id}" in route.request.url:
                time.sleep(0.35)
            route.continue_()

        page.route("**/api/v1/games/mines/session/*", delay_session_resume)
        page.goto(f"{frontend_base_url}/mines?title_code=mines_classic&embed=1", wait_until="domcontentloaded")

        overlay = page.locator(".mines-access-session-modal")
        assert overlay.get_by_text("Sto riallineando la mano con il server. Attendi qualche istante.").is_visible()

        page.wait_for_function(
            f"""
            () => window.localStorage.getItem('casinoking.current_session_id') === {json.dumps(active_game_session_id)}
            """
        )
        page.wait_for_function(
            """
            () => {
                const enabledCells = document.querySelectorAll('.board-cell:not(:disabled)').length;
                const betButton = Array.from(document.querySelectorAll('button')).find(
                    (button) => button.textContent?.trim() === 'Bet'
                );
                return enabledCells > 0 && Boolean(betButton?.hasAttribute('disabled'));
            }
            """
        )

        assert (
            page.evaluate("() => window.localStorage.getItem('casinoking.current_session_id')")
            == active_game_session_id
        )
        assert page.get_by_role("button", name="Bet").is_disabled()
        assert page.locator(".mines-access-session-modal").count() == 0

        browser.close()


@pytest.mark.integration
def test_mines_launch_token_auth_error_blocks_runtime_without_logout(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="browser-mines-launch-token-player")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})

        page.add_init_script(
            f"""
            () => {{
                window.localStorage.setItem('casinoking.access_token', {json.dumps(str(player['access_token']))});
                window.localStorage.setItem('casinoking.email', {json.dumps(str(player['email']))});
            }}
            """
        )

        def reject_launch_token(route) -> None:
            route.fulfill(
                status=401,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Game launch token is not valid",
                        },
                    }
                ),
            )

        page.route("**/api/v1/games/mines/launch-token", reject_launch_token)
        page.goto(f"{frontend_base_url}/mines?title_code=mines_classic&embed=1", wait_until="networkidle")
        page.get_by_role("button", name="Bet").click()

        overlay = page.locator(".mines-access-session-modal")
        assert overlay.get_by_text(
            "La sessione di gioco non è più allineata con il server. Ricarica la pagina per continuare in sicurezza."
        ).is_visible()
        assert page.get_by_role("button", name="Bet").is_disabled()
        assert (
            page.evaluate("() => window.localStorage.getItem('casinoking.access_token')")
            == str(player["access_token"])
        )

        browser.close()


@pytest.mark.integration
def test_mines_access_session_conflict_shows_expired_overlay_and_locks_surface(
    frontend_base_url: str,
    wait_for_frontend,
    create_authenticated_player,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    player = create_authenticated_player(prefix="browser-mines-access-timeout-player")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})

        page.add_init_script(
            f"""
            () => {{
                const originalSetInterval = window.setInterval.bind(window);
                window.setInterval = (handler, timeout, ...args) =>
                    originalSetInterval(handler, timeout >= 30000 ? 20 : timeout, ...args);
                window.localStorage.setItem('casinoking.access_token', {json.dumps(str(player['access_token']))});
                window.localStorage.setItem('casinoking.email', {json.dumps(str(player['email']))});
            }}
            """
        )

        def reject_access_ping(route) -> None:
            route.fulfill(
                status=409,
                content_type="application/json",
                body=json.dumps(
                    {
                        "success": False,
                        "error": {
                            "code": "GAME_STATE_CONFLICT",
                            "message": "Access session timed out",
                        },
                    }
                ),
            )

        page.route("**/api/v1/access-sessions/*/ping", reject_access_ping)
        page.goto(f"{frontend_base_url}/mines?title_code=mines_classic&embed=1", wait_until="networkidle")

        overlay = page.locator(".mines-access-session-modal")
        assert overlay.get_by_text("Sessione inattiva scaduta. Ricarica la pagina per continuare.").is_visible()
        assert page.get_by_role("button", name="Bet").is_disabled()

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
def test_admin_login_wrong_password_shows_visible_error(
    frontend_base_url: str,
    wait_for_frontend,
    create_admin_user,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="browser-admin-login-error")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1015, "height": 399})
        page.goto(f"{frontend_base_url}/admin/games/mines", wait_until="networkidle")
        page.get_by_label("Email").fill(str(admin_user["email"]))
        page.get_by_label("Password").fill("wrong-password")
        page.get_by_role("button", name="Sign in").click()

        alert = page.locator(".admin-login-status")
        alert.get_by_text("Invalid email or password.").wait_for(timeout=10_000)

        assert page.get_by_role("button", name="Sign in").is_visible()
        assert "Invalid email or password." in alert.inner_text()

        browser.close()


@pytest.mark.integration
def test_admin_mines_backoffice_shows_publish_workflow_on_full_width_surface(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    auth_headers,
    track_mines_variant_cleanup,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="browser-admin-backoffice")
    title_code = track_mines_variant_cleanup(
        _browser_duplicate_mines_variant(
            client,
            auth_headers,
            admin_user=admin_user,
        )
    )

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
        page.get_by_role("button", name="Games").wait_for()
        page.goto(
            f"{frontend_base_url}/admin/games/mines/titles/{title_code}",
            wait_until="networkidle",
        )
        page.get_by_text("Editor Status: Published").wait_for()

        save_button = page.get_by_role("button", name="Save draft")
        publish_button = page.get_by_role("button", name="Publish live")
        load_draft_button = page.get_by_role("button", name="Load saved draft")

        assert save_button.is_disabled()
        assert publish_button.is_disabled()

        metrics = page.evaluate(
            """
            () => {
                const panel = document.querySelector('.admin-panel-clean');
                const panelBox = panel?.getBoundingClientRect() ?? null;
                const publishButton = Array.from(document.querySelectorAll('button')).find(
                  (button) => button.textContent?.trim() === 'Publish live'
                );
                const saveButton = Array.from(document.querySelectorAll('button')).find(
                  (button) => button.textContent?.trim() === 'Save draft'
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

        page.get_by_role("button", name="Lobby card / Assets").click()
        page.get_by_role("heading", name="Lobby card").wait_for()
        page.get_by_text("No card").wait_for()
        page.get_by_text("When missing, the lobby uses the Mines fallback art.").wait_for()

        page.get_by_role("button", name="Rules HTML").click()
        rules_editor = page.locator("textarea").first
        original_value = rules_editor.input_value()
        updated_value = f"{original_value}\n<p>Smoke workflow update.</p>"
        rules_editor.fill(updated_value)

        page.get_by_text("Editor Status: Unsaved changes").wait_for()
        assert save_button.is_disabled() is False
        assert publish_button.is_disabled()

        with page.expect_response(
            lambda response: f"/api/v1/admin/games/titles/{title_code}/config" in response.url
            and response.request.method == "GET"
            and response.status == 200
        ):
            load_draft_button.click()

        page.get_by_text("Editor Status: Published").wait_for()
        assert save_button.is_disabled()
        assert publish_button.is_disabled()

        rules_editor = page.locator("textarea").first
        rules_editor.fill(updated_value)

        page.get_by_text("Editor Status: Unsaved changes").wait_for()
        assert save_button.is_disabled() is False
        assert publish_button.is_disabled()

        with page.expect_response(
            lambda response: f"/api/v1/admin/games/titles/{title_code}/config" in response.url
            and response.request.method == "PUT"
            and response.status == 200
        ):
            save_button.click()

        page.get_by_text("Editor Status: Draft ready").wait_for()
        assert save_button.is_disabled()
        assert publish_button.is_disabled() is False

        with page.expect_response(
            lambda response: f"/api/v1/admin/games/titles/{title_code}/config/publish" in response.url
            and response.request.method == "POST"
            and response.status == 200
        ):
            publish_button.click()

        page.get_by_text("Editor Status: Published").wait_for()
        assert save_button.is_disabled()
        assert publish_button.is_disabled()

        browser.close()


@pytest.mark.integration
def test_admin_finance_view_shows_bank_sessions_report_without_request_loop(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_admin_user,
    create_authenticated_player,
    create_published_mines_variant,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    admin_user = create_admin_user(prefix="browser-admin-finance-beta")
    player = create_authenticated_player(prefix="browser-admin-finance-player")
    published_title = create_published_mines_variant(
        title_code=f"browser_finance_{uuid4().hex[:8]}",
        display_name="Browser Finance Report",
    )
    title_code = str(published_title["title_code"])
    for index in range(26):
        access_session_id = _browser_create_access_session(
            client,
            auth_headers,
            access_token=str(player["access_token"]),
            title_code=title_code,
        )
        _browser_lose_round(
            client,
            auth_headers,
            db_helpers,
            access_token=str(player["access_token"]),
            idempotency_key=f"browser-admin-finance-round-{index}",
            grid_size=25,
            mine_count=3,
            access_session_id=access_session_id,
            title_code=title_code,
        )
        close_response = client.post(
            f"/access-sessions/{access_session_id}/close",
            headers=auth_headers(str(player["access_token"]), title_code=title_code),
        )
        assert close_response.status_code == 200, close_response.text

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        finance_request_count = 0
        finance_unauthorized_count = 0
        finance_mutation_request_count = 0
        finance_payloads: list[dict[str, object]] = []

        def capture_response(response) -> None:
            nonlocal finance_request_count, finance_unauthorized_count, finance_mutation_request_count
            if "/api/v1/admin/reports/financial/sessions" not in response.url:
                return
            if response.request.method != "GET":
                finance_mutation_request_count += 1
                return
            finance_request_count += 1
            if response.status == 401:
                finance_unauthorized_count += 1
            if response.status == 200 and "/api/v1/admin/reports/financial/sessions/" not in response.url:
                finance_payloads.append(response.json()["data"])

        page.on("response", capture_response)
        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
        page.get_by_label("Email").fill(str(admin_user["email"]))
        page.get_by_label("Password").fill(str(admin_user["password"]))
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("button", name="Finance").click()
        page.wait_for_timeout(1500)

        page.get_by_label("Player").fill(str(player["email"]))
        with page.expect_response(
            lambda response: "/api/v1/admin/reports/financial/sessions" in response.url
            and response.request.method == "GET"
            and f"email={str(player['email']).replace('@', '%40')}" in response.url
        ) as filtered_response_info:
            page.get_by_role("button", name="Filter").click()

        filtered_payload = filtered_response_info.value.json()["data"]
        page_size_select = page.get_by_label("Rows per page")

        assert page.get_by_role("button", name="Filter").count() == 1
        assert page.get_by_text("Bank session report").count() >= 1
        assert page.get_by_label("Player").count() == 1
        assert page.get_by_label("Wallet").count() == 1
        assert page.get_by_label("Transaction type").count() == 1
        assert page.get_by_label("Rows per page").count() == 1
        assert page.get_by_label("Start date").count() == 1
        assert page.get_by_label("End date").count() == 1
        assert page.get_by_label("Min bank delta").count() == 1
        assert page.get_by_label("Max bank delta").count() == 1
        assert page_size_select.input_value() == "50"
        assert page_size_select.locator("option").evaluate_all(
            "(nodes) => nodes.map((node) => node.value)"
        ) == ["25", "50", "100"]
        assert filtered_payload["pagination"] == {
            "page": 1,
            "limit": 50,
            "total_items": 26,
            "total_pages": 1,
        }
        assert len(filtered_payload["sessions"]) == 26
        assert all(session["user_email"] == str(player["email"]) for session in filtered_payload["sessions"])
        assert all(session["is_legacy"] is False for session in filtered_payload["sessions"])
        assert page.get_by_text(str(player["email"])).count() >= 1
        assert page.get_by_text("Page Bank Delta Total").count() == 1
        assert page.get_by_text("Page 1 of 1").count() >= 1

        with page.expect_response(
            lambda response: "/api/v1/admin/reports/financial/sessions" in response.url
            and response.request.method == "GET"
            and "limit=25" in response.url
        ) as page_size_response_info:
            page_size_select.select_option("25")

        page_one_payload = page_size_response_info.value.json()["data"]
        previous_button = page.get_by_role("button", name="Previous Page")
        next_button = page.get_by_role("button", name="Next")
        assert page_one_payload["pagination"] == {
            "page": 1,
            "limit": 25,
            "total_items": 26,
            "total_pages": 2,
        }
        assert len(page_one_payload["sessions"]) == 25
        assert "bank_delta" in page_one_payload["page_totals"]
        assert page.get_by_text("Page 1 of 2").count() >= 1
        assert previous_button.is_disabled()
        assert next_button.is_disabled() is False

        with page.expect_response(
            lambda response: "/api/v1/admin/reports/financial/sessions" in response.url
            and response.request.method == "GET"
            and "page=2" in response.url
            and "limit=25" in response.url
        ) as page_two_response_info:
            next_button.click()

        page_two_payload = page_two_response_info.value.json()["data"]
        assert page_two_payload["pagination"] == {
            "page": 2,
            "limit": 25,
            "total_items": 26,
            "total_pages": 2,
        }
        assert len(page_two_payload["sessions"]) == 1
        assert page_two_payload["sessions"][0]["user_email"] == str(player["email"])
        assert page.get_by_text("Page 2 of 2").count() >= 1
        assert previous_button.is_disabled() is False
        assert next_button.is_disabled()
        assert finance_payloads[-1]["pagination"]["page"] == 2

        with page.expect_response(
            lambda response: "/api/v1/admin/reports/financial/sessions/" in response.url
            and response.request.method == "GET"
        ) as detail_response_info:
            page.get_by_role("button", name="Round detail").first.click()

        detail_payload = detail_response_info.value.json()["data"]
        assert detail_payload["events"]
        first_event = detail_payload["events"][0]
        assert first_event["platform_round_id"]
        assert first_event["ledger_transaction_id"]
        assert page.get_by_text(first_event["platform_round_id"]).count() >= 1
        assert page.get_by_text(first_event["ledger_transaction_id"]).count() >= 1
        assert finance_request_count >= 4
        assert finance_request_count <= 7
        assert finance_unauthorized_count == 0
        assert finance_mutation_request_count == 0

        browser.close()


@pytest.mark.integration
def test_admin_stale_token_bootstrap_does_not_call_financial_report(
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
        finance_request_count = 0

        def capture_response(response) -> None:
            nonlocal finance_request_count
            if (
                "/api/v1/admin/reports/financial/sessions" in response.url
                and response.request.method == "GET"
            ):
                finance_request_count += 1

        page.on("response", capture_response)
        page.add_init_script(
            """
            () => {
                window.localStorage.setItem('casinoking.admin_access_token', 'stale-admin-token');
                window.localStorage.setItem('casinoking.admin_email', 'stale-admin@example.com');
            }
            """
        )
        page.goto(f"{frontend_base_url}/admin", wait_until="networkidle")
        page.wait_for_timeout(1200)

        assert page.get_by_role("button", name="Sign in").count() == 1
        assert finance_request_count == 0

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
        page.goto(f"{frontend_base_url}/mines?title_code=mines_classic&embed=1", wait_until="networkidle")
        _browser_complete_mines_onboarding(page)
        page.get_by_role("button", name=target_grid_label).click()

        mine_values = page.locator(".field").filter(has_text="Mines").get_by_role("button").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )

        assert mine_values == expected_values
        assert len(mine_values) <= 5

        browser.close()
