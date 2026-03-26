from __future__ import annotations


def test_admin_can_read_other_user_mines_session_snapshot(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-mines-admin-session")
    player = create_authenticated_player(prefix="integration-mines-player-session")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-mines-admin-session-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()["data"]

    session_response = client.get(
        f"/games/mines/session/{start_payload['game_session_id']}",
        headers=auth_headers(admin_user["access_token"]),
    )

    assert session_response.status_code == 200
    payload = session_response.json()["data"]
    assert payload["game_session_id"] == start_payload["game_session_id"]
    assert payload["status"] == "active"
    assert payload["grid_size"] == 25
    assert payload["mine_count"] == 3
    assert payload["bet_amount"] == "5.000000"
    assert payload["wallet_type"] == "cash"
    assert payload["safe_reveals_count"] == 0
    assert payload["multiplier_current"] == "1.0000"
    assert payload["wallet_balance_after_start"] == start_payload[
        "wallet_balance_after"
    ]
    assert payload["ledger_transaction_id"] == start_payload["ledger_transaction_id"]
    assert payload["created_at"]
    assert payload["closed_at"] is None
