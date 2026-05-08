from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import shutil

import pytest


playwright = pytest.importorskip("playwright.sync_api")


def _find_chromium_executable() -> str | None:
    candidates = [
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        "/snap/bin/chromium",
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
        page.add_init_script(
            """
            ({ accessToken, email, firstName, lastName, fiscalCode, phoneNumber }) => {
                window.localStorage.setItem('casinoking.access_token', accessToken);
                window.localStorage.setItem('casinoking.email', email);
                window.localStorage.setItem('casinoking.first_name', firstName);
                window.localStorage.setItem('casinoking.last_name', lastName);
                window.localStorage.setItem('casinoking.fiscal_code', fiscalCode);
                window.localStorage.setItem('casinoking.phone_number', phoneNumber);
            }
            """,
            {
                "accessToken": str(player["access_token"]),
                "email": str(player["email"]),
                "firstName": str(player["first_name"]),
                "lastName": str(player["last_name"]),
                "fiscalCode": str(player["fiscal_code"]),
                "phoneNumber": str(player["phone_number"]),
            },
        )
        page.goto(f"{frontend_base_url}/account", wait_until="networkidle")
        page.get_by_role("tab", name="Estratto Conto").click()

        expect_positive_delta = f"+{(won_payout - Decimal('2.000000')).quantize(Decimal('0.01'))} CHIP"

        page.wait_for_function(
            """
            () => {
                const cards = Array.from(document.querySelectorAll('.player-account-statement-card'));
                return cards.length >= 2 && cards.every((card) => {
                    const text = (card.textContent || '').replace(/\\s+/g, ' ').trim();
                    return text.includes('Risultato') && text.includes('Mostra dettaglio');
                });
            }
            """
        )

        statement_cards = page.locator(".player-account-statement-card")
        summary_values = statement_cards.evaluate_all(
            """
            (nodes) => nodes.slice(0, 2).map((node) => {
                const result = node.querySelector(
                    '.player-account-statement-metric strong.is-positive, ' +
                    '.player-account-statement-metric strong.is-negative, ' +
                    '.player-account-statement-metric strong.is-neutral'
                );
                return {
                    text: (result?.textContent || '').replace(/\\s+/g, ' ').trim(),
                    color: result ? window.getComputedStyle(result).color : '',
                };
            }))
            """
        )

        assert summary_values[0]["text"] == "-1.00 CHIP"
        assert summary_values[0]["color"] == "rgb(252, 165, 165)"
        assert summary_values[1]["text"] == expect_positive_delta
        assert summary_values[1]["color"] == "rgb(134, 239, 172)"

        statement_cards.nth(0).get_by_role("button", name="Mostra dettaglio").click()

        detail_table = statement_cards.nth(0).locator(".player-account-round-table")
        page.wait_for_function(
            """
            () => {
                const table = document.querySelector('.player-account-statement-card .player-account-round-table');
                const headers = Array.from(table?.querySelectorAll('thead tr th') || []);
                const rows = table?.querySelectorAll('tbody > tr') || [];
                return headers.some((cell) => (cell.textContent || '').trim() === 'Payout') && rows.length >= 1;
            }
            """
        )

        headers = detail_table.locator("thead tr th").evaluate_all(
            "(nodes) => nodes.map((node) => (node.textContent || '').trim())"
        )
        assert headers == [
            "Data round",
            "Round",
            "Config",
            "Celle safe",
            "Puntata",
            "Esito",
            "Payout",
        ]

        browser.close()
