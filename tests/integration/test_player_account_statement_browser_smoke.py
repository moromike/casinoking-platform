from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import shutil
from uuid import uuid4

import pytest

from app.modules.games.boxe.randomness import generate_step_outcome


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


@pytest.mark.integration
def test_player_account_statement_shows_summary_cards_and_round_detail(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    del wait_for_frontend

    player = create_authenticated_player(prefix="browser-account-delta")

    first_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "browser-account-delta-start-win",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
        },
    )
    assert first_start_response.status_code == 200, first_start_response.text
    won_session_id = first_start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(won_session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": won_session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "browser-account-delta-cashout-win",
        },
        json={"game_session_id": won_session_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    won_payout = Decimal(cashout_response.json()["data"]["payout_amount"])

    second_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "browser-account-delta-start-loss",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert second_start_response.status_code == 200, second_start_response.text
    lost_session_id = second_start_response.json()["data"]["game_session_id"]

    mine_cell = db_helpers.get_mine_positions(lost_session_id)[0]
    loss_reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": lost_session_id,
            "cell_index": mine_cell,
        },
    )
    assert loss_reveal_response.status_code == 200, loss_reveal_response.text

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1365, "height": 768})
        _seed_player_storage(page, player)
        page.goto(f"{frontend_base_url}/account", wait_until="networkidle")
        page.wait_for_function(
            """
            () => document.querySelector('.site-v3-account-summary-card') &&
                (document.body.textContent || '').includes('Saldo reale')
            """
        )

        page.get_by_role("tab", name="Cassa").click()
        page.wait_for_function(
            """
            () => {
                const rows = Array.from(document.querySelectorAll('.site-v3-account-row'));
                const text = (document.body.textContent || '').replace(/\\s+/g, ' ').trim();
                return rows.length >= 1 && text.includes('Cassa') && text.includes('Gioco');
            }
            """
        )

        page.locator(".site-v3-account-row-button:not(:disabled)").first.click()
        page.locator(".site-v3-account-detail-list").first.wait_for(timeout=15_000)

        page.get_by_role("tab", name="Storico gioco").click()
        page.wait_for_function(
            """
            () => {
                const rows = Array.from(document.querySelectorAll('.site-v3-account-row'));
                const text = (document.body.textContent || '').replace(/\\s+/g, ' ').trim();
                return rows.length >= 2 && text.includes('Mines') && text.includes('Rivedi mano');
            }
            """
        )
        assert f"{won_payout.quantize(Decimal('0.01'))} CHIP" in page.locator("body").inner_text()

        page.get_by_role("button", name="Rivedi mano").first.click()
        page.locator(".site-v3-replay-meta").first.wait_for(timeout=15_000)
        assert page.locator("body").evaluate("document.body.scrollWidth <= window.innerWidth")

        browser.close()


@pytest.mark.integration
def test_player_account_boxe_replay_pyramid_fits_eight_row_statement_detail(
    frontend_base_url: str,
    wait_for_frontend,
    client,
    create_authenticated_player,
    auth_headers,
    db_connection,
) -> None:
    del wait_for_frontend

    _seed_boxe_catalog_for_account(db_connection)
    player = create_authenticated_player(prefix="browser-account-boxe-replay")
    headers = auth_headers(player["access_token"], include_game_launch_token=False)
    _create_completed_boxe_cashout_round(
        client=client,
        headers=headers,
        db_connection=db_connection,
        rows=8,
    )

    chromium_executable = _find_chromium_executable()
    if chromium_executable is None:
        pytest.skip("Chromium executable not available for browser smoke test.")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium_executable,
        )
        page = browser.new_page(viewport={"width": 1180, "height": 820})
        _seed_player_storage(page, player)
        page.goto(f"{frontend_base_url}/account", wait_until="networkidle")
        page.get_by_role("tab", name="Storico gioco").click()

        page.wait_for_function(
            """
            () => Array.from(document.querySelectorAll('.site-v3-account-row')).some((card) => {
                const text = (card.textContent || '').replace(/\\s+/g, ' ').trim();
                return text.includes('BOXE') && text.includes('Rivedi mano');
            })
            """
        )

        boxe_card = page.locator(".site-v3-account-row").filter(has_text="BOXE").first
        boxe_card.get_by_role("button", name="Rivedi mano").click()
        page.wait_for_function(
            """
            () => {
                const replay = document.querySelector('.site-v3-replay-boxe-pyramid');
                const text = (replay?.textContent || '').replace(/\\s+/g, ' ').trim();
                return text.length > 0 &&
                    replay.querySelectorAll('.site-v3-replay-boxe-row').length === 8 &&
                    replay.querySelectorAll('.site-v3-replay-cell').length >= 8;
            }
            """
        )

        metrics = page.evaluate(
            """
            () => {
                const viewer = document.querySelector('.site-v3-replay-panel');
                const pyramid = viewer.querySelector('.site-v3-replay-boxe-pyramid');
                const rows = Array.from(viewer.querySelectorAll('.site-v3-replay-boxe-row'));
                const cells = Array.from(viewer.querySelectorAll('.site-v3-replay-cell'));
                const rowWidths = rows.map((row) => row.getBoundingClientRect().width);
                const cellWidths = cells.map((cell) => cell.getBoundingClientRect().width);
                return {
                    panelWidth: viewer.getBoundingClientRect().width,
                    cellMax: Math.max(...cellWidths),
                    cellMin: Math.min(...cellWidths),
                    cellWidths: cellWidths.slice(0, 18),
                    maxCellCount: Math.max(...rows.map((row) => row.querySelectorAll('.site-v3-replay-cell').length)),
                    pyramidOverflowX: pyramid.scrollWidth - pyramid.clientWidth,
                    pyramidWidth: pyramid.getBoundingClientRect().width,
                    rowCount: rows.length,
                    rowTemplates: rows.map((row) => window.getComputedStyle(row).gridTemplateColumns),
                    viewerOverflowX: viewer.scrollWidth - viewer.clientWidth,
                    widestRowWidth: Math.max(...rowWidths),
                };
            }
            """
        )
        metrics_debug = json.dumps(metrics, sort_keys=True)

        assert metrics["rowCount"] == 8
        assert metrics["maxCellCount"] == 9
        assert metrics["cellMin"] >= 17, metrics_debug
        assert metrics["cellMax"] <= (metrics["pyramidWidth"] / 2) + 2, metrics_debug
        assert metrics["widestRowWidth"] <= metrics["pyramidWidth"] + 2, metrics_debug
        assert metrics["pyramidOverflowX"] <= 2, metrics_debug
        assert metrics["viewerOverflowX"] <= 2, metrics_debug
        assert metrics["panelWidth"] >= metrics["widestRowWidth"], metrics_debug

        browser.close()


def _seed_player_storage(page, player: dict[str, object]) -> None:
    player_storage = {
        "accessToken": str(player["access_token"]),
        "email": str(player["email"]),
        "firstName": str(player["first_name"]),
        "lastName": str(player["last_name"]),
        "fiscalCode": str(player["fiscal_code"]),
        "phoneNumber": str(player["phone_number"]),
    }
    page.add_init_script(
        f"""
        (() => {{
            const player = {json.dumps(player_storage)};
            window.localStorage.setItem('casinoking.access_token', player.accessToken);
            window.localStorage.setItem('casinoking.email', player.email);
            window.localStorage.setItem('casinoking.first_name', player.firstName);
            window.localStorage.setItem('casinoking.last_name', player.lastName);
            window.localStorage.setItem('casinoking.fiscal_code', player.fiscalCode);
            window.localStorage.setItem('casinoking.phone_number', player.phoneNumber);
        }})();
        """
    )


def _seed_boxe_catalog_for_account(db_connection) -> None:
    with db_connection.cursor() as cursor:
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


def _create_completed_boxe_cashout_round(
    *,
    client,
    headers: dict[str, str],
    db_connection,
    rows: int,
) -> str:
    key_prefix = f"account-boxe-replay-{uuid4().hex}"
    start_response = client.post(
        "/games/boxe/start",
        headers={**headers, "Idempotency-Key": f"{key_prefix}-start"},
        json={
            "title_code": "boxe001",
            "rows": rows,
            "difficulty": "easy",
            "bet_amount": "1.00",
            "wallet_source": "demo",
            "client_seed": f"seed-{key_prefix}",
        },
    )
    assert start_response.status_code == 200, start_response.text
    round_id = start_response.json()["data"]["round_id"]
    row, position = _boxe_pick_for_step(
        db_connection=db_connection,
        round_id=round_id,
        step=1,
        want_safe=True,
    )
    reveal_response = client.post(
        "/games/boxe/reveal",
        headers={**headers, "Idempotency-Key": f"{key_prefix}-reveal"},
        json={"round_id": round_id, "row": row, "position": position},
    )
    assert reveal_response.status_code == 200, reveal_response.text
    cashout_response = client.post(
        "/games/boxe/cashout",
        headers={**headers, "Idempotency-Key": f"{key_prefix}-cashout"},
        json={"round_id": round_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    return str(round_id)


def _boxe_pick_for_step(
    *,
    db_connection,
    round_id: str,
    step: int,
    want_safe: bool,
) -> tuple[int, int]:
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM boxe_rounds WHERE id = %s", (round_id,))
        round_row = cursor.fetchone()
    assert round_row is not None

    row_index = step - 1
    cell_count = int(round_row["rows_count"]) - row_index + 1
    for position in range(cell_count):
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
            return row_index, position
    raise AssertionError(f"No BOXE pick found for want_safe={want_safe}")
