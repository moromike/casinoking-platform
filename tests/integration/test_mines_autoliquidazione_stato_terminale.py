from __future__ import annotations
pytest_plugins = ["tests.fixtures.mines"]

from uuid import uuid4

from tests.integration.helpers import create_game_access_session




def test_mines_autoliquidazione_chiude_il_round_con_stato_terminale(
    client,
    create_authenticated_player,
    create_published_mines_variant,
    mines_auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="mines-autoliquidazione")
    title = create_published_mines_variant(
        display_name="Mines Autoliquidazione Stato Terminale"
    )
    headers = mines_auth_headers(
        str(player["access_token"]), title_code=str(title["title_code"])
    )
    access_session_id = create_game_access_session(
        client,
        headers,
        game_code="mines",
        title_code=str(title["title_code"]),
    )

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"mines-autoliquidazione-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
            "title_code": str(title["title_code"]),
        },
    )
    assert start_response.status_code == 200, start_response.text
    round_id = str(start_response.json()["data"]["game_session_id"])

    close_response = client.post(
        f"/access-sessions/{access_session_id}/close", headers=headers
    )
    assert close_response.status_code == 200, close_response.text

    round_row = db_helpers.fetchone(
        """
        SELECT status, closed_at
        FROM mines_game_rounds
        WHERE id = %s
        """,
        (round_id,),
    )
    assert round_row is not None
    # CANCELLED, non WON: la liquidazione d'ufficio RESTITUISCE la puntata, non
    # premia. Misurato l'8/09/2026 su 278 righe: incasso == puntata su tutte.
    # Chiamarla vincita gonfierebbe win rate e RTP di partite mai vinte.
    assert round_row["status"] == "cancelled"
    assert round_row["closed_at"] is not None
