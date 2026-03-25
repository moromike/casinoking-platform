from __future__ import annotations


def test_signup_wallets_start_reconciled(
    create_player,
    db_helpers,
) -> None:
    player = create_player(prefix="integration-reconciliation-signup")

    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "1000.000000",
        "ledger_balance": "1000.000000",
        "drift": "0.000000",
    }
    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "bonus") == {
        "wallet_type": "bonus",
        "balance_snapshot": "0.000000",
        "ledger_balance": "0.000000",
        "drift": "0.000000",
    }


def test_mines_win_keeps_cash_wallet_reconciled(
    client,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    player = create_authenticated_player(prefix="integration-reconciliation-mines")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-reconciliation-mines-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["data"]["game_session_id"]

    mine_positions = set(db_helpers.get_mine_positions(session_id))
    safe_cell = next(index for index in range(25) if index not in mine_positions)

    reveal_response = client.post(
        "/games/mines/reveal",
        headers=auth_headers(player["access_token"]),
        json={
            "game_session_id": session_id,
            "cell_index": safe_cell,
        },
    )
    assert reveal_response.status_code == 200

    cashout_response = client.post(
        "/games/mines/cashout",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-reconciliation-mines-cashout",
        },
        json={"game_session_id": session_id},
    )
    assert cashout_response.status_code == 200

    assert db_helpers.get_wallet_reconciliation(str(player["user_id"]), "cash") == {
        "wallet_type": "cash",
        "balance_snapshot": "1000.114500",
        "ledger_balance": "1000.114500",
        "drift": "0.000000",
    }


def test_admin_bonus_grant_keeps_bonus_wallet_reconciled(
    client,
    create_admin_user,
    create_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-reconciliation-admin")
    target_user = create_player(prefix="integration-reconciliation-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/bonus-grants",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-reconciliation-bonus-grant",
        },
        json={
            "amount": "50.000000",
            "reason": "reconciliation_check",
        },
    )
    assert response.status_code == 200

    assert db_helpers.get_wallet_reconciliation(str(target_user["user_id"]), "bonus") == {
        "wallet_type": "bonus",
        "balance_snapshot": "50.000000",
        "ledger_balance": "50.000000",
        "drift": "0.000000",
    }
