from __future__ import annotations


def test_admin_users_require_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-admin-forbidden")

    response = client.get(
        "/admin/users",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_admin_ledger_report_requires_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-admin-report-forbidden")

    response = client.get(
        "/admin/reports/ledger",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_mines_backoffice_config_requires_admin_role_for_read(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-mines-backoffice-read")

    response = client.get(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_mines_backoffice_config_requires_admin_role_for_write(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-mines-backoffice-write")

    response = client.put(
        "/admin/games/mines/backoffice-config",
        headers=auth_headers(player["access_token"]),
        json={
            "rules_sections": {
                "ways_to_win": "<p>Pick and collect.</p>",
                "payout_display": "<p>Payout ladder.</p>",
                "settings_menu": "<p>Settings.</p>",
                "bet_collect": "<p>Bet and collect.</p>",
                "balance_display": "<p>Balance.</p>",
                "general": "<p>General.</p>",
                "history": "<p>History.</p>",
            },
            "published_grid_sizes": [9],
            "published_mine_counts": {"9": [1, 3, 5]},
            "default_mine_counts": {"9": 3},
            "ui_labels": {
                "demo": {
                    "bet": "Bet",
                    "bet_loading": "Betting...",
                    "collect": "Collect",
                    "collect_loading": "Collecting...",
                    "home": "Home",
                    "fullscreen": "Fullscreen",
                    "game_info": "Game info",
                },
                "real": {
                    "bet": "Bet",
                    "bet_loading": "Betting...",
                    "collect": "Collect",
                    "collect_loading": "Collecting...",
                    "home": "Home",
                    "fullscreen": "Fullscreen",
                    "game_info": "Game info",
                },
            },
            "board_assets": {
                "safe_icon_data_url": None,
                "mine_icon_data_url": None,
            },
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_mines_backoffice_publish_requires_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-mines-backoffice-publish")

    response = client.post(
        "/admin/games/mines/backoffice-config/publish",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_admin_can_read_other_user_transaction_detail(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-admin-ledger-detail")
    player = create_authenticated_player(prefix="contract-ledger-detail-player")

    player_transactions_response = client.get(
        "/ledger/transactions",
        headers=auth_headers(player["access_token"]),
    )
    assert player_transactions_response.status_code == 200
    transaction_id = player_transactions_response.json()["data"][0]["id"]

    detail_response = client.get(
        f"/ledger/transactions/{transaction_id}",
        headers=auth_headers(admin_user["access_token"]),
    )

    assert detail_response.status_code == 200
    payload = detail_response.json()["data"]
    assert payload["id"] == transaction_id
    assert payload["transaction_type"] == "signup_credit"
    assert len(payload["entries"]) >= 2


def test_admin_suspend_requires_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-admin-suspend-forbidden")

    response = client.post(
        f"/admin/users/{player['user_id']}/suspend",
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_admin_adjustment_requires_idempotency_key(
    client,
    create_admin_user,
    create_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-admin")
    target_user = create_player(prefix="contract-admin-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/adjustments",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "wallet_type": "bonus",
            "direction": "credit",
            "amount": "10.000000",
            "reason": "manual_compensation",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Idempotency-Key header is required",
        },
    }


def test_admin_bonus_grant_requires_idempotency_key(
    client,
    create_admin_user,
    create_player,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-bonus-admin")
    target_user = create_player(prefix="contract-bonus-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/bonus-grants",
        headers=auth_headers(admin_user["access_token"]),
        json={
            "amount": "25.000000",
            "reason": "manual promotional credit",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Idempotency-Key header is required",
        },
    }


def test_admin_fairness_rotate_requires_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-fairness-rotate-forbidden")

    response = client.post(
        "/games/mines/fairness/rotate",
        headers={
            **auth_headers(player["access_token"]),
            "Idempotency-Key": "contract-fairness-rotate",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }


def test_admin_fairness_rotate_requires_idempotency_key(
    client,
    create_admin_user,
    auth_headers,
) -> None:
    admin_user = create_admin_user(prefix="contract-fairness-rotate-admin")

    response = client.post(
        "/games/mines/fairness/rotate",
        headers=auth_headers(admin_user["access_token"]),
    )

    assert response.status_code == 422
    assert response.json() == {
        "success": False,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Idempotency-Key header is required",
        },
    }


def test_admin_fairness_verify_requires_admin_role(
    client,
    create_authenticated_player,
    auth_headers,
) -> None:
    player = create_authenticated_player(prefix="contract-fairness-verify-forbidden")

    response = client.get(
        "/games/mines/verify",
        params={"session_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(player["access_token"]),
    )

    assert response.status_code == 403
    assert response.json() == {
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": "Role is not valid for this endpoint",
        },
    }
