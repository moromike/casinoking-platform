from __future__ import annotations


def test_wallet_detail_matches_materialized_snapshot_before_and_after_mines_start(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-wallet-detail")

    def _wallet_rows() -> dict[str, dict[str, object]]:
        response = client.get(
            "/wallets",
            headers=auth_headers(player["access_token"]),
        )
        assert response.status_code == 200
        return {
            row["wallet_type"]: row
            for row in response.json()["data"]
        }

    def _wallet_detail(wallet_type: str) -> dict[str, object]:
        response = client.get(
            f"/wallets/{wallet_type}",
            headers=auth_headers(player["access_token"]),
        )
        assert response.status_code == 200
        return response.json()["data"]

    initial_rows = _wallet_rows()
    assert _wallet_detail("cash") == initial_rows["cash"]
    assert _wallet_detail("bonus") == initial_rows["bonus"]

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-wallet-detail-mines-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200

    cash_detail = _wallet_detail("cash")
    bonus_detail = _wallet_detail("bonus")
    updated_rows = _wallet_rows()

    assert cash_detail == updated_rows["cash"]
    assert bonus_detail == updated_rows["bonus"]
    assert cash_detail["balance_snapshot"] == "995.000000"
    assert bonus_detail["balance_snapshot"] == "0.000000"
    assert db_helpers.get_wallet_balance(str(player["user_id"]), "cash") == "995.000000"
    assert db_helpers.get_wallet_balance(str(player["user_id"]), "bonus") == "0.000000"
