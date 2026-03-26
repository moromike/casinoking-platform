from __future__ import annotations


def test_admin_ledger_transactions_include_other_users(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-ledger-admin")
    player = create_authenticated_player(prefix="contract-ledger-player")

    player_transactions_response = client.get(
        "/ledger/transactions",
        headers=auth_headers(player["access_token"]),
    )
    assert player_transactions_response.status_code == 200
    player_transaction_id = player_transactions_response.json()["data"][0]["id"]

    admin_transactions_response = client.get(
        "/ledger/transactions",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert admin_transactions_response.status_code == 200

    admin_transaction_ids = {
        row["id"] for row in admin_transactions_response.json()["data"]
    }
    assert player_transaction_id in admin_transaction_ids
