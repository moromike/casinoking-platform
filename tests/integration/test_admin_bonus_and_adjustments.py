from __future__ import annotations


def test_admin_bonus_grant_updates_bonus_wallet_and_audit(
    client,
    create_admin_user,
    create_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-bonus")
    target_user = create_player(prefix="integration-bonus-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/bonus-grants",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-bonus-grant",
        },
        json={
            "amount": "50.000000",
            "reason": "manual promotional credit",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == {
        "target_user_id": str(target_user["user_id"]),
        "wallet_type": "bonus",
        "direction": "credit",
        "amount": "50.000000",
        "wallet_balance_after": "50.000000",
        "ledger_transaction_id": payload["ledger_transaction_id"],
        "admin_action_id": payload["admin_action_id"],
    }

    duplicate_response = client.post(
        f"/admin/users/{target_user['user_id']}/bonus-grants",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-bonus-grant",
        },
        json={
            "amount": "50.000000",
            "reason": "manual promotional credit",
        },
    )
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["data"] == payload

    assert db_helpers.get_wallet_balance(str(target_user["user_id"]), "bonus") == "50.000000"

    admin_action_row = db_helpers.fetchone(
        """
        SELECT action_type, wallet_type, direction, amount, reason, wallet_balance_after
        FROM admin_actions
        WHERE id = %s
        """,
        (payload["admin_action_id"],),
    )
    assert admin_action_row == {
        "action_type": "bonus_grant",
        "wallet_type": "bonus",
        "direction": "credit",
        "amount": 50,
        "reason": "manual promotional credit",
        "wallet_balance_after": 50,
    }

    transaction_row = db_helpers.fetchone(
        """
        SELECT transaction_type
        FROM ledger_transactions
        WHERE id = %s
        """,
        (payload["ledger_transaction_id"],),
    )
    assert transaction_row == {"transaction_type": "bonus_grant"}

    entries = [
        {
            "account_code": row["account_code"],
            "entry_side": row["entry_side"],
            "amount": f"{row['amount']:.6f}",
        }
        for row in db_helpers.get_transaction_entries(payload["ledger_transaction_id"])
    ]
    assert sorted(entries, key=lambda item: (item["entry_side"], item["account_code"])) == sorted([
        {
            "account_code": "PROMO_RESERVE",
            "entry_side": "debit",
            "amount": "50.000000",
        },
        {
            "account_code": f"PLAYER_BONUS_{target_user['user_id']}",
            "entry_side": "credit",
            "amount": "50.000000",
        },
    ], key=lambda item: (item["entry_side"], item["account_code"]))


def test_admin_cash_adjustment_debit_updates_wallet_and_audit(
    client,
    create_admin_user,
    create_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-adjust")
    target_user = create_player(prefix="integration-adjust-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/adjustments",
        headers={
            **auth_headers(admin_user["access_token"]),
            "Idempotency-Key": "integration-admin-adjustment",
        },
        json={
            "wallet_type": "cash",
            "direction": "debit",
            "amount": "10.000000",
            "reason": "manual_compensation",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["wallet_type"] == "cash"
    assert payload["direction"] == "debit"
    assert payload["amount"] == "10.000000"
    assert payload["wallet_balance_after"] == "990.000000"

    assert db_helpers.get_wallet_balance(str(target_user["user_id"]), "cash") == "990.000000"

    transaction_row = db_helpers.fetchone(
        """
        SELECT transaction_type
        FROM ledger_transactions
        WHERE id = %s
        """,
        (payload["ledger_transaction_id"],),
    )
    assert transaction_row == {"transaction_type": "admin_adjustment"}

    entries = [
        {
            "account_code": row["account_code"],
            "entry_side": row["entry_side"],
            "amount": f"{row['amount']:.6f}",
        }
        for row in db_helpers.get_transaction_entries(payload["ledger_transaction_id"])
    ]
    assert sorted(entries, key=lambda item: (item["entry_side"], item["account_code"])) == sorted([
        {
            "account_code": f"PLAYER_CASH_{target_user['user_id']}",
            "entry_side": "debit",
            "amount": "10.000000",
        },
        {
            "account_code": "HOUSE_CASH",
            "entry_side": "credit",
            "amount": "10.000000",
        },
    ], key=lambda item: (item["entry_side"], item["account_code"]))
