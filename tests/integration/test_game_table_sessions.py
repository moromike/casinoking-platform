from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


def test_table_session_reserves_and_consumes_loss(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-loss")
    headers = auth_headers(player["access_token"])

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
        },
    )
    assert create_response.status_code == 200, create_response.text
    table_session = create_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"integration-table-loss-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "4.000000",
            "wallet_type": "cash",
            "table_session_id": table_session["id"],
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    reserved_response = client.get(f"/table-sessions/{table_session['id']}", headers=headers)
    assert reserved_response.status_code == 200
    reserved_session = reserved_response.json()["data"]
    assert reserved_session["table_balance_amount"] == "6.000000"
    assert reserved_session["loss_reserved_amount"] == "4.000000"
    assert reserved_session["loss_consumed_amount"] == "0.000000"
    assert reserved_session["loss_remaining_amount"] == "6.000000"

    mine_cell = db_helpers.get_mine_positions(session_id)[0]
    loss_response = client.post(
        "/games/mines/reveal",
        headers=headers,
        json={
            "game_session_id": session_id,
            "cell_index": mine_cell,
        },
    )
    assert loss_response.status_code == 200, loss_response.text

    consumed_response = client.get(f"/table-sessions/{table_session['id']}", headers=headers)
    assert consumed_response.status_code == 200
    consumed_session = consumed_response.json()["data"]
    assert consumed_session["table_balance_amount"] == "6.000000"
    assert consumed_session["loss_reserved_amount"] == "0.000000"
    assert consumed_session["loss_consumed_amount"] == "4.000000"
    assert consumed_session["loss_remaining_amount"] == "6.000000"


def test_table_session_releases_reserved_amount_on_cashout(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-cashout")
    headers = auth_headers(player["access_token"])

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "10.000000",
        },
    )
    assert create_response.status_code == 200, create_response.text
    table_session = create_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"integration-table-cashout-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "4.000000",
            "wallet_type": "cash",
            "table_session_id": table_session["id"],
        },
    )
    assert start_response.status_code == 200, start_response.text
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)
    reveal_response = client.post(
        "/games/mines/reveal",
        headers=headers,
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200, reveal_response.text

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **headers,
            "Idempotency-Key": f"integration-table-cashout-{uuid4().hex}",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200, cashout_response.text
    payout_amount = Decimal(cashout_response.json()["data"]["payout_amount"])

    released_response = client.get(f"/table-sessions/{table_session['id']}", headers=headers)
    assert released_response.status_code == 200
    released_session = released_response.json()["data"]
    expected_table_balance = Decimal("6.000000") + payout_amount
    assert released_session["table_balance_amount"] == f"{expected_table_balance:.6f}"
    assert released_session["loss_reserved_amount"] == "0.000000"
    assert released_session["loss_consumed_amount"] == "0.000000"
    assert released_session["loss_remaining_amount"] == "10.000000"


def test_table_session_rejects_bet_over_remaining_limit(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-table-limit")
    headers = auth_headers(player["access_token"])

    create_response = client.post(
        "/table-sessions",
        headers=headers,
        json={
            "game_code": "mines",
            "wallet_type": "cash",
            "table_budget_amount": "3.000000",
        },
    )
    assert create_response.status_code == 200, create_response.text
    table_session = create_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": f"integration-table-limit-start-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "4.000000",
            "wallet_type": "cash",
            "table_session_id": table_session["id"],
        },
    )
    assert start_response.status_code == 422
    assert start_response.json()["error"]["message"] == "Table session limit exceeded"
