from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
import shutil
from urllib.parse import urlencode
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
import pytest

from app.modules.games.boxe.randomness import generate_step_outcome


playwright = pytest.importorskip("playwright.sync_api")


@pytest.mark.parametrize(
    ("mode", "wallet_source", "expected_wallet_label"),
    [
        ("demo", None, "DEMO"),
        ("real_cash", "real", "CASH"),
        ("real_bonus", "bonus", "BONUS"),
    ],
)
def test_boxe_boot_modes_reach_gameplay(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
    mode: str,
    wallet_source: str | None,
    expected_wallet_label: str,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix=f"boxe-ui-boot-{mode}")
    if wallet_source == "bonus":
        _grant_bonus_balance(database_url, str(player["user_id"]), Decimal("25.000000"))
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        if mode != "demo":
            _seed_player_storage(
                page,
                access_token=str(player["access_token"]),
                email=str(player["email"]),
            )

        _open_boxe_gameplay(
            page,
            frontend_base_url,
            mode=mode,
            wallet_source=wallet_source,
        )

        page.get_by_test_id("boxe-gameplay").wait_for()
        page.locator(".boxe-balance-strip em").filter(
            has_text=expected_wallet_label,
        ).wait_for()
        assert page.get_by_test_id("boxe-primary-action").is_visible()
        browser.close()


@pytest.mark.parametrize(
    ("mode", "wallet_source", "wallet_type"),
    [
        ("real_cash", "real", "cash"),
        ("real_bonus", "bonus", "bonus"),
    ],
)
def test_boxe_real_wallet_cashout_updates_selected_wallet(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
    mode: str,
    wallet_source: str,
    wallet_type: str,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix=f"boxe-ui-{wallet_type}")
    player_id = str(player["user_id"])
    if wallet_type == "bonus":
        _grant_bonus_balance(database_url, player_id, Decimal("25.000000"))
    before_balance = _wallet_balance(database_url, player_id, wallet_type)
    before_bet_sum = _platform_boxe_bet_sum(database_url, player_id, wallet_type)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(
            page,
            access_token=str(player["access_token"]),
            email=str(player["email"]),
        )
        _open_boxe_gameplay(
            page,
            frontend_base_url,
            mode=mode,
            wallet_source=wallet_source,
        )
        _configure_four_row_easy_round(page)

        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=player_id,
            path_kind="retry",
            frontend_base_url=frontend_base_url,
            mode=mode,
            wallet_source=wallet_source,
        )
        pick = _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=True)
        assert pick is not None
        row, position = pick
        page.get_by_test_id(f"boxe-cell-{row}-{position}").click()
        page.get_by_test_id("boxe-primary-action").wait_for()
        page.get_by_test_id("boxe-primary-action").click()

        page.get_by_text("completed cashout").wait_for()
        browser.close()

    after_balance = _wallet_balance(database_url, player_id, wallet_type)
    debited_bets = _platform_boxe_bet_sum(database_url, player_id, wallet_type) - before_bet_sum
    payout = _round_final_payout(database_url, round_id)
    assert after_balance == before_balance - debited_bets + payout


def test_boxe_demo_boot_reaches_idle_gameplay(frontend_base_url: str, database_url: str) -> None:
    _seed_boxe_catalog(database_url)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        requests: list[str] = []
        page.on("request", lambda request: requests.append(request.url))

        _open_boxe_gameplay(page, frontend_base_url)

        page.get_by_test_id("boxe-gameplay").wait_for()
        assert page.get_by_test_id("boxe-primary-action").is_enabled()
        assert page.get_by_text("98% RTP").is_visible()
        assert any("/api/v1/games/boxe/config?title_code=boxe001" in url for url in requests)
        browser.close()


def test_boxe_demo_safe_sequence_cashout_resets_to_bet(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-cashout")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _capture_boxe_audio_events(page)
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)

        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="cashout",
        )
        path = _safe_path_within_ui(database_url, round_id, steps=3)
        assert path is not None
        for row, position in path:
            page.get_by_test_id(f"boxe-cell-{row}-{position}").click()
            page.get_by_test_id("boxe-primary-action").wait_for()

        page.get_by_test_id("boxe-primary-action").click()
        page.get_by_text("completed cashout").wait_for()
        assert page.get_by_test_id("boxe-rows-4").is_enabled()
        assert {"bet_placed", "safe_reveal", "cashout_won"}.issubset(
            set(page.evaluate("window.__boxeAudioEvents"))
        )
        browser.close()


def test_boxe_demo_loss_reveals_current_row_opaque(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-loss")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _capture_boxe_audio_events(page)
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)

        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="loss",
        )
        pick = _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=False)
        assert pick is not None
        row, position = pick
        page.get_by_test_id(f"boxe-cell-{row}-{position}").click()

        page.get_by_text("failed mine").wait_for()
        assert page.locator(".boxe-pyramid-cell.mine").count() == 1
        assert page.locator(".boxe-pyramid-row.loss-row .boxe-pyramid-cell.opaque").count() == 2
        assert {"bet_placed", "mine_reveal"}.issubset(
            set(page.evaluate("window.__boxeAudioEvents"))
        )
        browser.close()


def test_boxe_demo_top_row_auto_collect(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-top")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _capture_boxe_audio_events(page)
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)

        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="top-row",
        )
        path = _safe_path_within_ui(database_url, round_id, steps=4)
        assert path is not None
        for row, position in path:
            page.get_by_test_id(f"boxe-cell-{row}-{position}").click()

        page.get_by_text("completed top row").wait_for()
        assert page.get_by_test_id("boxe-rows-4").is_enabled()
        assert "top_row_won" in page.evaluate("window.__boxeAudioEvents")
        browser.close()


def test_boxe_reveal_retry_reuses_action(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-retry")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)
        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="retry",
        )
        pick = _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=True)
        assert pick is not None
        row, position = pick

        failed_once = {"value": False}

        def fail_first_reveal(route):
            if not failed_once["value"]:
                failed_once["value"] = True
                route.abort()
                return
            route.continue_()

        page.route("**/api/v1/games/boxe/reveal", fail_first_reveal)
        page.get_by_test_id(f"boxe-cell-{row}-{position}").click()
        page.get_by_test_id("boxe-retry-action").wait_for()
        page.get_by_test_id("boxe-retry-action").click()

        page.locator(".boxe-pyramid-cell.safe").wait_for()
        assert page.locator(".boxe-pyramid-cell.safe").count() == 1
        browser.close()


def test_boxe_mobile_portrait_starts_round(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-mobile")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)

        _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="retry",
        )

        page.get_by_text("active").wait_for()
        assert page.get_by_test_id("boxe-cell-0-0").is_visible()
        browser.close()


def test_boxe_reduced_motion_disables_reveal_animations(
    frontend_base_url: str,
    database_url: str,
    create_authenticated_player,
) -> None:
    _seed_boxe_catalog(database_url)
    player = create_authenticated_player(prefix="boxe-ui-reduced")
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.emulate_media(reduced_motion="reduce")
        _seed_player_storage(page, access_token=str(player["access_token"]), email=str(player["email"]))
        _open_boxe_gameplay(page, frontend_base_url)
        _configure_four_row_easy_round(page)
        round_id = _start_round_with_ui_path(
            page,
            database_url,
            player_id=str(player["user_id"]),
            path_kind="retry",
        )
        pick = _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=True)
        assert pick is not None
        row, position = pick
        page.get_by_test_id(f"boxe-cell-{row}-{position}").click()
        safe_cell = page.locator(".boxe-pyramid-cell.safe").first
        safe_cell.wait_for()
        assert safe_cell.evaluate("node => getComputedStyle(node).animationName") == "none"
        assert page.get_by_test_id("boxe-payout-current").evaluate(
            "node => getComputedStyle(node).animationName"
        ) == "none"
        browser.close()


def test_boxe_short_landscape_rotation_gate(frontend_base_url: str, database_url: str) -> None:
    _seed_boxe_catalog(database_url)
    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium_executable)
        page = browser.new_page(viewport={"width": 882, "height": 344})
        _open_boxe_gameplay(page, frontend_base_url)

        page.get_by_role("status", name="Ruota il dispositivo").wait_for()
        assert page.get_by_test_id("boxe-gameplay").is_visible()
        browser.close()


def _open_boxe_gameplay(
    page,
    frontend_base_url: str,
    *,
    mode: str = "demo",
    wallet_source: str | None = None,
) -> None:
    query = {
        "title_code": "boxe001",
        "mode": mode,
    }
    if wallet_source is not None:
        query["wallet_source"] = wallet_source
    page.goto(
        f"{frontend_base_url}/boxe?{urlencode(query)}",
        wait_until="networkidle",
    )
    page.locator(".game-provider-bootstrap-skip").click()
    page.get_by_role("button", name="Continua").click()
    page.get_by_test_id("boxe-table-balance-gate").get_by_role(
        "button",
        name="Entra nel gioco",
    ).click()
    page.get_by_test_id("boxe-gameplay").wait_for()


def _configure_four_row_easy_round(page) -> None:
    page.get_by_test_id("boxe-rows-4").click()
    page.get_by_test_id("boxe-difficulty-easy").click()
    page.get_by_test_id("boxe-bet-input").fill("1")


def _start_round_with_ui_path(
    page,
    database_url: str,
    *,
    player_id: str,
    path_kind: str,
    frontend_base_url: str | None = None,
    mode: str = "demo",
    wallet_source: str | None = None,
) -> str:
    for _attempt in range(12):
        page.get_by_test_id("boxe-primary-action").click()
        page.get_by_text("active").wait_for()
        round_id = _latest_boxe_round_id(database_url, player_id=player_id)
        if path_kind == "cashout" and _safe_path_within_ui(database_url, round_id, steps=3):
            return round_id
        if path_kind == "top-row" and _safe_path_within_ui(database_url, round_id, steps=4):
            return round_id
        if path_kind == "loss" and _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=False):
            return round_id
        if path_kind == "retry" and _pick_for_step_within_ui(database_url, round_id, step=1, want_safe=True):
            return round_id
        page.reload(wait_until="networkidle")
        _open_boxe_gameplay(
            page,
            frontend_base_url or page.url.split("/boxe", maxsplit=1)[0],
            mode=mode,
            wallet_source=wallet_source,
        )
        _configure_four_row_easy_round(page)
    raise AssertionError(f"No UI-compatible BOXE path found for {path_kind}")


def _latest_boxe_round_id(database_url: str, *, player_id: str) -> str:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM boxe_rounds
                WHERE player_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (player_id,),
            )
            row = cursor.fetchone()
    assert row is not None
    return str(row["id"])


def _wallet_balance(database_url: str, player_id: str, wallet_type: str) -> Decimal:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT balance_snapshot
                FROM wallet_accounts
                WHERE user_id = %s
                  AND wallet_type = %s
                """,
                (player_id, wallet_type),
            )
            row = cursor.fetchone()
    assert row is not None
    return Decimal(row["balance_snapshot"]).quantize(Decimal("0.000001"))


def _platform_boxe_bet_sum(database_url: str, player_id: str, wallet_type: str) -> Decimal:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(bet_amount), 0) AS total_bet
                FROM platform_rounds
                WHERE game_code = 'boxe'
                  AND user_id = %s
                  AND wallet_type = %s
                """,
                (player_id, wallet_type),
            )
            row = cursor.fetchone()
    assert row is not None
    return Decimal(row["total_bet"]).quantize(Decimal("0.000001"))


def _round_final_payout(database_url: str, round_id: str) -> Decimal:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT final_payout_amount
                FROM boxe_rounds
                WHERE id = %s
                """,
                (round_id,),
            )
            row = cursor.fetchone()
    assert row is not None
    return Decimal(row["final_payout_amount"]).quantize(Decimal("0.000001"))


def _grant_bonus_balance(database_url: str, player_id: str, amount: Decimal) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE wallet_accounts
                SET balance_snapshot = balance_snapshot + %s
                WHERE user_id = %s
                  AND wallet_type = 'bonus'
                """,
                (amount, player_id),
            )


def _safe_path_within_ui(
    database_url: str,
    round_id: str,
    *,
    steps: int,
) -> list[tuple[int, int]] | None:
    path: list[tuple[int, int]] = []
    for step in range(1, steps + 1):
        pick = _pick_for_step_within_ui(database_url, round_id, step=step, want_safe=True)
        if pick is None:
            return None
        path.append(pick)
    return path


def _pick_for_step_within_ui(
    database_url: str,
    round_id: str,
    *,
    step: int,
    want_safe: bool,
) -> tuple[int, int] | None:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
            round_row = cursor.fetchone()
    assert round_row is not None
    for position in range(3):
        outcome = generate_step_outcome(
            rows=int(round_row["rows_count"]),
            difficulty=str(round_row["difficulty"]),
            step=step,
            selected_box_index=position,
            server_seed=str(round_row["server_seed"]),
            client_seed=str(round_row["client_seed"]),
            nonce=int(round_row["nonce"]),
        )
        if outcome.safe is want_safe:
            return step - 1, position
    return None


def _seed_player_storage(page, *, access_token: str, email: str) -> None:
    page.add_init_script(
        f"""
        window.localStorage.setItem('casinoking.access_token', {json.dumps(access_token)});
        window.localStorage.setItem('casinoking.email', {json.dumps(email)});
        window.localStorage.removeItem('casinoking.boxe_current_session_id');
        """
    )


def _capture_boxe_audio_events(page) -> None:
    page.add_init_script(
        """
        window.__boxeAudioEvents = [];
        window.addEventListener('boxe:audio-event', (event) => {
          window.__boxeAudioEvents.push(event.detail.event);
        });
        """
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


def _seed_boxe_catalog(database_url: str) -> None:
    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO game_engines (engine_code, display_name, runtime_module, status)
                VALUES ('boxe', 'BOXE', 'app.modules.games.boxe', 'active')
                ON CONFLICT (engine_code) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    runtime_module = EXCLUDED.runtime_module,
                    status = 'active'
                """
            )
            cursor.execute(
                """
                INSERT INTO game_titles (
                    title_code,
                    engine_code,
                    display_name,
                    status,
                    is_master,
                    source_title_code
                )
                VALUES
                    ('boxe', 'boxe', 'BOXE Master', 'active', true, NULL),
                    ('boxe001', 'boxe', 'BOXE 001', 'active', false, 'boxe')
                ON CONFLICT (title_code) DO UPDATE
                SET engine_code = EXCLUDED.engine_code,
                    display_name = EXCLUDED.display_name,
                    status = 'active',
                    is_master = EXCLUDED.is_master,
                    source_title_code = EXCLUDED.source_title_code,
                    updated_at = NOW()
                """
            )
            cursor.execute(
                """
                INSERT INTO site_titles (
                    site_code,
                    title_code,
                    position,
                    status,
                    lobby_visibility,
                    demo_enabled,
                    real_enabled,
                    lobby_display_name,
                    lobby_description,
                    featured
                )
                VALUES
                    ('casinoking', 'boxe', 900, 'active', 'hidden', false, false, 'BOXE Master', 'Master BOXE', false),
                    ('casinoking', 'boxe001', 901, 'active', 'visible', true, true, 'BOXE', 'BOXE test title', false)
                ON CONFLICT (site_code, title_code) DO UPDATE
                SET status = 'active',
                    lobby_visibility = EXCLUDED.lobby_visibility,
                    demo_enabled = EXCLUDED.demo_enabled,
                    real_enabled = EXCLUDED.real_enabled,
                    lobby_display_name = EXCLUDED.lobby_display_name,
                    lobby_description = EXCLUDED.lobby_description,
                    featured = EXCLUDED.featured,
                    updated_at = NOW()
                """
            )
