from __future__ import annotations


def test_admin_ledger_report_exposes_recent_transactions_and_reconciliation(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-report-admin")
    player = create_authenticated_player(prefix="integration-report-player")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-report-mines-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200

    report_response = client.get(
        "/admin/reports/ledger",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert report_response.status_code == 200

    payload = report_response.json()["data"]
    assert payload["summary"]["recent_transaction_count"] >= 2
    assert payload["summary"]["balanced_transaction_count"] >= 2
    assert payload["summary"]["wallet_count"] >= 2
    assert payload["summary"]["wallets_with_drift_count"] == 0
    assert "recent_transactions" in payload
    assert "wallet_reconciliation" in payload

    player_transactions = [
        row
        for row in payload["recent_transactions"]
        if row["user_email"] == player["email"]
    ]
    transaction_types = {row["transaction_type"] for row in player_transactions}
    assert "signup_credit" in transaction_types
    assert "bet" in transaction_types
    assert all(
        row["entry_count"] >= 2 and row["total_debit"] == row["total_credit"]
        for row in player_transactions
    )

    player_reconciliation = [
        row
        for row in payload["wallet_reconciliation"]
        if row["user_email"] == player["email"]
    ]
    assert len(player_reconciliation) == 2
    for row in player_reconciliation:
        assert row["currency_code"] == "CHIP"
        assert row["drift"] == "0.000000"
        assert row["balance_snapshot"] == row["ledger_balance"]


def test_admin_can_open_transaction_detail_from_ledger_report(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-report-detail-admin")
    player = create_authenticated_player(prefix="integration-report-detail-player")

    start_response = client.post(
        "/games/mines/start",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "integration-report-detail-start",
        },
        json={
            "grid_size": 25,
            "mine_count": 3,
            "bet_amount": "5.000000",
            "wallet_type": "cash",
        },
    )
    assert start_response.status_code == 200

    report_response = client.get(
        "/admin/reports/ledger",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert report_response.status_code == 200
    report_payload = report_response.json()["data"]

    player_transaction = next(
        row
        for row in report_payload["recent_transactions"]
        if row["user_email"] == player["email"] and row["transaction_type"] == "bet"
    )

    detail_response = client.get(
        f"/ledger/transactions/{player_transaction['id']}",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert detail_response.status_code == 200

    detail_payload = detail_response.json()["data"]
    assert detail_payload["id"] == player_transaction["id"]
    assert detail_payload["transaction_type"] == "bet"
    assert detail_payload["idempotency_key"].startswith("mines:start:")
    assert detail_payload["idempotency_key"].endswith(":integration-report-detail-start")
    assert len(detail_payload["entries"]) == player_transaction["entry_count"]

    account_codes = {entry["ledger_account_code"] for entry in detail_payload["entries"]}
    assert f"PLAYER_CASH_{player['user_id']}" in account_codes
    assert "HOUSE_CASH" in account_codes


def test_admin_can_drill_down_transaction_detail_from_ledger_report(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="integration-report-detail-admin")
    player = create_authenticated_player(prefix="integration-report-detail-player")

    report_response = client.get(
        "/admin/reports/ledger",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert report_response.status_code == 200

    report_payload = report_response.json()["data"]
    player_transaction = next(
        row
        for row in report_payload["recent_transactions"]
        if row["user_email"] == player["email"]
        and row["transaction_type"] == "signup_credit"
    )

    detail_response = client.get(
        f"/ledger/transactions/{player_transaction['id']}",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert detail_response.status_code == 200

    detail_payload = detail_response.json()["data"]
    assert detail_payload["id"] == player_transaction["id"]
    assert detail_payload["transaction_type"] == "signup_credit"
    assert len(detail_payload["entries"]) == player_transaction["entry_count"]

    account_codes = {entry["ledger_account_code"] for entry in detail_payload["entries"]}
    assert f"PLAYER_CASH_{player['user_id']}" in account_codes
    assert "HOUSE_CASH" in account_codes
