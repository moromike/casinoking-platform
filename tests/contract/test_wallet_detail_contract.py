from __future__ import annotations


def test_wallet_detail_contract_returns_cash_and_bonus_snapshots(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-wallet-detail")

    for wallet_type, expected_balance in (
        ("cash", "1000.000000"),
        ("bonus", "0.000000"),
    ):
        response = client.get(
            f"/wallets/{wallet_type}",
            headers=auth_headers(player["access_token"]),
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload == {
            "wallet_type": wallet_type,
            "currency_code": "CHIP",
            "balance_snapshot": expected_balance,
            "status": "active",
            "ledger_account_code": f"PLAYER_{wallet_type.upper()}_{player['user_id']}",
        }


def test_wallet_detail_unknown_wallet_type_is_not_found(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-wallet-missing")

    response = client.get(
        "/wallets/vip",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Wallet not found",
        },
    }
