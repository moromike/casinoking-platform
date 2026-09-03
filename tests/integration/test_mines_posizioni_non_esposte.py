"""SIC-08: le posizioni delle mine non sono persistite mentre il round e' aperto.

Verifica che:
- durante un round aperto la riga del database non contiene ne'
  mine_positions_json ne' rng_material (sono ricalcolati al volo da
  seed+nonce+parametri);
- il gioco funziona lo stesso (scoperta di una casella sicura, incasso);
- a round chiuso le posizioni sono materializzate nella riga e la
  verifica di correttezza (/games/mines/verify) continua a funzionare.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


def _start_real_round(
    *,
    client,
    auth_headers,
    player,
    title_code: str,
    bet_amount: str = "1.000000",
    grid_size: int = 9,
    mine_count: int = 1,
) -> dict[str, str]:
    """Create access/table sessions and start a real round."""
    headers_with_token = auth_headers(player["access_token"], title_code=title_code)

    access_resp = client.post(
        "/access-sessions",
        headers=headers_with_token,
        json={"game_code": "mines", "title_code": title_code},
    )
    assert access_resp.status_code == 200, access_resp.text
    access_session_id = access_resp.json()["data"]["id"]

    table_resp = client.post(
        "/table-sessions",
        headers=headers_with_token,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
            "access_session_id": access_session_id,
            "title_code": title_code,
        },
    )
    assert table_resp.status_code == 200, table_resp.text
    table_session_id = table_resp.json()["data"]["id"]

    start_resp = client.post(
        "/games/mines/start",
        headers={
            **headers_with_token,
            "Idempotency-Key": f"sic08-start-{uuid4().hex}",
        },
        json={
            "access_session_id": access_session_id,
            "table_session_id": table_session_id,
            "bet_amount": bet_amount,
            "grid_size": grid_size,
            "mine_count": mine_count,
            "wallet_type": "cash",
            "title_code": title_code,
        },
    )
    assert start_resp.status_code == 200, start_resp.text
    game_session_id = start_resp.json()["data"]["game_session_id"]

    return {
        "access_session_id": access_session_id,
        "table_session_id": table_session_id,
        "game_session_id": game_session_id,
    }


def _fetch_round_row(db_helpers, game_session_id: str) -> dict[str, object]:
    row = db_helpers.fetchone(
        """
        SELECT status, mine_positions_json, rng_material, board_hash
        FROM mines_game_rounds
        WHERE id = %s
        """,
        (game_session_id,),
    )
    assert row is not None
    return row


def test_posizioni_non_esposte_mentre_round_aperto(
    client,
    create_authenticated_player,
    auth_headers,
    create_published_mines_variant,
    db_helpers,
) -> None:
    """Durante un round aperto la riga non contiene posizioni ne' rng_material."""
    player = create_authenticated_player(prefix="sic08-open-round")
    published_title = create_published_mines_variant(display_name="SIC08 Open Round")
    title_code = str(published_title["title_code"])

    ids = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
        title_code=title_code,
    )

    row = _fetch_round_row(db_helpers, ids["game_session_id"])
    assert row["status"] == "active"
    assert row["mine_positions_json"] is None
    assert row["rng_material"] is None
    # L'impegno (commitment) resta persistito fin dall'apertura.
    assert row["board_hash"]


def test_gioco_funziona_e_posizioni_materializzate_alla_chiusura(
    client,
    create_authenticated_player,
    create_admin_user,
    auth_headers,
    create_published_mines_variant,
    db_helpers,
) -> None:
    """Reveal + cashout funzionano; a round chiuso le posizioni ci sono e verify passa."""
    player = create_authenticated_player(prefix="sic08-close-round")
    admin_user = create_admin_user(prefix="sic08-close-round-admin")
    published_title = create_published_mines_variant(display_name="SIC08 Close Round")
    title_code = str(published_title["title_code"])

    ids = _start_real_round(
        client=client,
        auth_headers=auth_headers,
        player=player,
        title_code=title_code,
    )
    headers = auth_headers(player["access_token"], title_code=title_code)

    row = _fetch_round_row(db_helpers, ids["game_session_id"])
    assert row["mine_positions_json"] is None
    assert row["rng_material"] is None

    # get_mine_positions ricalcola le posizioni da seed+nonce+parametri.
    mine_positions = set(db_helpers.get_mine_positions(ids["game_session_id"]))
    safe_cell = next(index for index in range(9) if index not in mine_positions)

    reveal_resp = client.post(
        "/games/mines/reveal",
        headers=headers,
        json={"game_session_id": ids["game_session_id"], "cell_index": safe_cell},
    )
    assert reveal_resp.status_code == 200, reveal_resp.text
    reveal_data = reveal_resp.json()["data"]
    assert reveal_data["result"] == "safe"
    potential_payout = Decimal(reveal_data["potential_payout"])

    # Dopo una scoperta sicura il round e' ancora aperto: niente posizioni.
    row = _fetch_round_row(db_helpers, ids["game_session_id"])
    assert row["status"] == "active"
    assert row["mine_positions_json"] is None
    assert row["rng_material"] is None

    cashout_resp = client.post(
        "/games/mines/cashout",
        headers={
            **headers,
            "Idempotency-Key": f"sic08-cashout-{uuid4().hex}",
        },
        json={"game_session_id": ids["game_session_id"]},
    )
    assert cashout_resp.status_code == 200, cashout_resp.text
    cashout_data = cashout_resp.json()["data"]
    assert cashout_data["status"] == "won"
    assert Decimal(str(cashout_data["payout_amount"])) == potential_payout
    assert sorted(cashout_data["mine_positions"]) == sorted(mine_positions)

    # A round chiuso le posizioni e rng_material sono materializzati.
    row = _fetch_round_row(db_helpers, ids["game_session_id"])
    assert row["status"] == "won"
    assert sorted(row["mine_positions_json"]) == sorted(mine_positions)
    assert row["rng_material"]

    # La verifica di correttezza del round chiuso continua a funzionare.
    verify_resp = client.get(
        "/games/mines/verify",
        params={"session_id": ids["game_session_id"]},
        headers=auth_headers(admin_user["access_token"]),
    )
    assert verify_resp.status_code == 200, verify_resp.text
    verify_data = verify_resp.json()["data"]
    assert verify_data["verified"] is True
    assert verify_data["server_seed_hash_match"] is True
    assert verify_data["board_hash_match"] is True
    assert verify_data["mine_positions_match"] is True
    assert sorted(verify_data["stored_mine_positions"]) == sorted(mine_positions)
