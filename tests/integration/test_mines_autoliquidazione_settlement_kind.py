from __future__ import annotations

from tests.integration.test_session_cascade_close import (
    _create_active_mines_table_session_and_round,
)


def test_mines_autoliquidazione_con_progresso_registra_auto_cashout(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
    create_published_mines_variant,
) -> None:
    player = create_authenticated_player(prefix="mines-auto-cashout-kind")
    title = create_published_mines_variant(
        display_name="Mines Autoliquidazione Settlement Kind"
    )
    title_code = str(title["title_code"])
    headers = auth_headers(player["access_token"], title_code=title_code)
    ids = _create_active_mines_table_session_and_round(
        client=client,
        headers=headers,
        bet_amount="4.000000",
        grid_size=9,
        mine_count=1,
        title_code=title_code,
    )

    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(9) if index not in mine_positions)
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=headers,
        json={
            "game_session_id": ids["game_session_id"],
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    close_response = client.post(
        f"/access-sessions/{ids['access_session_id']}/close",
        headers=headers,
    )
    assert close_response.status_code == 200, close_response.text
    auto_cashout = close_response.json()["data"]["auto_cashout"]
    assert auto_cashout["settlement_mode"] == "cashout"

    ledger_row = db_helpers.fetchone(
        """
        SELECT metadata_json
        FROM ledger_transactions
        WHERE id = %s
        """,
        (auto_cashout["ledger_transaction_id"],),
    )
    assert ledger_row is not None
    assert ledger_row["metadata_json"]["settlement_kind"] == "auto_cashout"
