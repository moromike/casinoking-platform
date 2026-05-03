from __future__ import annotations

from uuid import uuid4


def test_mines_recent_sessions_history_returns_latest_rounds_with_terminal_states(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-session-history")

    first_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-history-start-win-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
        },
    )
    assert first_start_response.status_code == 200
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
    assert reveal_response.status_code == 200

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-history-cashout-win-{uuid4().hex}",
        },
        json={"game_session_id": won_session_id},
    )
    assert cashout_response.status_code == 200
    won_payout = cashout_response.json()["data"]["payout_amount"]

    second_start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-history-start-loss-{uuid4().hex}",
        },
        json={
            "grid_size": 9,
            "mine_count": 1,
            "bet_amount": "1.000000",
            "wallet_type": "cash",
        },
    )
    assert second_start_response.status_code == 200
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
    assert loss_reveal_response.status_code == 200

    history_response = client.get(
        "/games/mines/sessions",
        headers=auth_headers(player["access_token"]),
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()["data"]

    assert [entry["game_session_id"] for entry in history_payload[:2]] == [
        lost_session_id,
        won_session_id,
    ]

    latest_loss = history_payload[0]
    assert latest_loss["status"] == "lost"
    assert latest_loss["grid_size"] == 9
    assert latest_loss["mine_count"] == 1
    assert latest_loss["bet_amount"] == "1.000000"
    assert latest_loss["safe_reveals_count"] == 0
    assert latest_loss["revealed_cells_count"] == 1
    assert latest_loss["potential_payout"] == "0.000000"
    assert latest_loss["closed_at"] is not None

    latest_win = history_payload[1]
    assert latest_win["status"] == "won"
    assert latest_win["grid_size"] == 25
    assert latest_win["mine_count"] == 3
    assert latest_win["bet_amount"] == "2.000000"
    assert latest_win["safe_reveals_count"] == 1
    assert latest_win["revealed_cells_count"] == 1
    assert latest_win["potential_payout"] == won_payout
    assert latest_win["closed_at"] is not None


def test_mines_recent_sessions_history_includes_access_session_payload(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="integration-session-history-access-session")

    create_response = client.post(
        "/access-sessions",
        headers=auth_headers(player["access_token"]),
        json={"game_code": "mines"},
    )
    assert create_response.status_code == 200
    access_session = create_response.json()["data"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": f"integration-history-access-session-start-{uuid4().hex}",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "2.000000",
            "wallet_type": "cash",
            "access_session_id": access_session["id"],
        },
    )
    assert start_response.status_code == 200

    history_response = client.get(
        "/games/mines/sessions",
        headers=auth_headers(player["access_token"]),
    )
    assert history_response.status_code == 200
    latest_entry = history_response.json()["data"][0]

    assert latest_entry["access_session_id"] == access_session["id"]
    assert latest_entry["access_session"]["id"] == access_session["id"]
    assert latest_entry["access_session"]["game_code"] == "mines"
    assert latest_entry["access_session"]["status"] == "active"
    assert latest_entry["access_session"]["started_at"] == access_session["started_at"]
    assert isinstance(latest_entry["access_session"]["last_activity_at"], str)
    assert latest_entry["access_session"]["last_activity_at"] >= access_session["last_activity_at"]
    assert latest_entry["access_session"]["ended_at"] is None
