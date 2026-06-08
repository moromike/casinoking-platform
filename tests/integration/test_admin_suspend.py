from __future__ import annotations


def test_admin_suspend_updates_status_and_blocks_player_access(
    client,
    create_admin_user,
    create_authenticated_player,
    auth_headers,
    db_helpers,
) -> None:
    admin_user = create_admin_user(prefix="integration-admin-suspend")
    target_user = create_authenticated_player(prefix="integration-suspend-target")

    response = client.post(
        f"/admin/users/{target_user['user_id']}/suspend",
        headers=auth_headers(admin_user["access_token"]),
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload == {
        "target_user_id": str(target_user["user_id"]),
        "email": target_user["email"],
        "role": "player",
        "status": "suspended",
        "created_at": payload["created_at"],
    }

    user_row = db_helpers.fetchone(
        """
        SELECT status
        FROM users
        WHERE id = %s
        """,
        (target_user["user_id"],),
    )
    assert user_row == {"status": "suspended"}

    duplicate_response = client.post(
        f"/admin/users/{target_user['user_id']}/suspend",
        headers=auth_headers(admin_user["access_token"]),
    )
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["data"]["status"] == "suspended"

    login_response = client.post(
        "/auth/login",
        json={
            "email": target_user["email"],
            "password": target_user["password"],
        },
    )
    assert login_response.status_code == 403
    login_payload = login_response.json()
    assert login_payload["success"] is False
    assert login_payload["error"]["code"] == "FORBIDDEN"
    assert login_payload["error"]["message"] == "Account is not active"

    wallet_response = client.get(
        "/wallets",
        headers=auth_headers(target_user["access_token"]),
    )
    assert wallet_response.status_code == 403
    wallet_payload = wallet_response.json()
    assert wallet_payload["success"] is False
    assert wallet_payload["error"]["code"] == "FORBIDDEN"
    assert wallet_payload["error"]["message"] == "Account is not active"
