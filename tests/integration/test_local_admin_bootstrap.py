from __future__ import annotations

from uuid import uuid4

from app.modules.auth.service import ensure_local_admin


def test_ensure_local_admin_creates_admin_and_can_authenticate(
    client,
    auth_headers,
) -> None:
    email = f"local-admin-{uuid4().hex[:10]}@example.com"
    password = f"StrongPass-{uuid4().hex[:12]}"

    result = ensure_local_admin(email=email, password=password)

    assert result["created"] is True
    assert result["role"] == "admin"
    assert result["password_reset"] is False

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["data"]["access_token"]

    admin_response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )
    assert admin_response.status_code == 200, admin_response.text


def test_ensure_local_admin_promotes_existing_user_and_resets_password(
    create_player,
    client,
    auth_headers,
) -> None:
    player = create_player(prefix="promote-admin")
    new_password = f"StrongPass-{uuid4().hex[:12]}"

    result = ensure_local_admin(email=str(player["email"]), password=new_password)

    assert result["created"] is False
    assert result["role"] == "admin"
    assert result["password_reset"] is True
    assert result["user_id"] == player["user_id"]

    old_login_response = client.post(
        "/auth/login",
        json={"email": player["email"], "password": player["password"]},
    )
    assert old_login_response.status_code == 401, old_login_response.text

    new_login_response = client.post(
        "/auth/login",
        json={"email": player["email"], "password": new_password},
    )
    assert new_login_response.status_code == 200, new_login_response.text
    token = new_login_response.json()["data"]["access_token"]

    admin_response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )
    assert admin_response.status_code == 200, admin_response.text
