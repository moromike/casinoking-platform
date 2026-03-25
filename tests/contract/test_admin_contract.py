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
