from __future__ import annotations


def test_admin_can_drill_down_from_session_snapshot_to_ledger_transaction_detail(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-session-drilldown")
    player = create_authenticated_player(prefix="integration-player-session-drilldown")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-admin-session-drilldown-start",
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
    session_payload = session_response.json()["data"]
    assert session_payload["game_session_id"] == start_payload["game_session_id"]
    assert session_payload["status"] == "active"
    assert session_payload["wallet_type"] == "cash"
    assert session_payload["ledger_transaction_id"] == start_payload[
        "ledger_transaction_id"
    ]
    assert session_payload["wallet_balance_after_start"] == start_payload[
        "wallet_balance_after"
    ]

    transaction_response = client.get(
        f"/ledger/transactions/{session_payload['ledger_transaction_id']}",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert transaction_response.status_code == 200
    transaction_payload = transaction_response.json()["data"]
    assert transaction_payload["id"] == session_payload["ledger_transaction_id"]
    assert transaction_payload["transaction_type"] == "bet"
    assert transaction_payload["reference_type"] == "game_session"
    assert transaction_payload["reference_id"] == session_payload["game_session_id"]
    assert transaction_payload["idempotency_key"].startswith("mines:start:")
    assert transaction_payload["idempotency_key"].endswith(
        ":integration-admin-session-drilldown-start"
    )

    db_entries = db_helpers.get_transaction_entries(transaction_payload["id"])
    assert [
        {
            "ledger_account_code": row["account_code"],
            "entry_side": row["entry_side"],
            "amount": f"{row['amount']:.6f}",
        }
        for row in db_entries
    ] == [
        {
            "ledger_account_code": row["ledger_account_code"],
            "entry_side": row["entry_side"],
            "amount": row["amount"],
        }
        for row in transaction_payload["entries"]
    ]

    assert {row["ledger_account_code"] for row in transaction_payload["entries"]} == {
        f"PLAYER_CASH_{player['user_id']}",
        "HOUSE_CASH",
    }
