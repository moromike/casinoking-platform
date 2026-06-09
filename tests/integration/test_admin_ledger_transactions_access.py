from __future__ import annotations

from tests.integration.helpers import create_game_access_session


def test_admin_ledger_transactions_match_database_transaction_count(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-ledger-admin")
    player = create_authenticated_player(prefix="integration-ledger-player")

    headers = auth_headers(player["access_token"])
    title_code = auth_headers.implicit_title_code() or "mines_auth_default"
    access_session_id = create_game_access_session(
        client, headers, game_code="mines", title_code=title_code
    )

    start_response = client.post(
        "/games/mines/start",
        headers={
            **headers,
            "Idempotency-Key": "integration-ledger-admin-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
            "access_session_id": access_session_id,
        },
    )
    assert start_response.status_code == 200

    response = client.get(
        "/ledger/transactions",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert response.status_code == 200
    payload = response.json()["data"]

    db_count = db_helpers.fetchone(
        """
        SELECT COUNT(*) AS transaction_count
        FROM ledger_transactions
        """,
        (),
    )
    assert db_count is not None
    assert len(payload) == db_count["transaction_count"]

    player_rows = [
        row for row in payload if row["transaction_type"] == "signup_credit"
    ]
    assert any(row["id"] == player["bootstrap_transaction_id"] for row in player_rows)
    assert any(row["transaction_type"] == "bet" for row in payload)
