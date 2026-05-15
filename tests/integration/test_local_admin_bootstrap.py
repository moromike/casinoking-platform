from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

import pytest

from app.db import config as db_config_module
from app.db import connection as db_connection_module
from app.modules.auth.service import AuthValidationError, ensure_local_admin


@pytest.fixture(autouse=True)
def _use_test_database_url_for_bootstrap(database_url):
    original_db_config = db_config_module.database_config
    original_connection_config = db_connection_module.database_config
    patched_db_config = replace(
        db_config_module.database_config,
        database_url=database_url,
    )
    db_config_module.database_config = patched_db_config
    db_connection_module.database_config = patched_db_config
    yield
    db_config_module.database_config = original_db_config
    db_connection_module.database_config = original_connection_config


def test_ensure_local_admin_creates_admin_and_can_authenticate(
    client,
    auth_headers,
    create_admin_user,
) -> None:
    admin_user = create_admin_user(prefix="local-admin")
    email = str(admin_user["email"])
    password = str(admin_user["password"])

    login_response = client.post(
        "/admin/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["data"]["access_token"]

    admin_response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )
    assert admin_response.status_code == 200, admin_response.text


def test_ensure_local_admin_refuses_protected_human_admin_account() -> None:
    with pytest.raises(AuthValidationError, match="protected human admin account"):
        ensure_local_admin(
            email="admin@example.com",
            password=f"StrongPass-{uuid4().hex[:12]}",
        )


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
        "/admin/auth/login",
        json={"email": player["email"], "password": new_password},
    )
    assert new_login_response.status_code == 200, new_login_response.text
    token = new_login_response.json()["data"]["access_token"]

    admin_response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )
    assert admin_response.status_code == 200, admin_response.text


def test_player_and_admin_login_flows_are_role_scoped(
    client,
    create_player,
    create_admin_user,
) -> None:
    player = create_player(prefix="auth-split-player")
    admin_user = create_admin_user(prefix="auth-split-admin")
    admin_email = str(admin_user["email"])
    admin_password = str(admin_user["password"])

    player_on_admin_response = client.post(
        "/admin/auth/login",
        json={"email": player["email"], "password": player["password"]},
    )
    assert player_on_admin_response.status_code == 403, player_on_admin_response.text
    assert player_on_admin_response.json()["error"]["message"] == "Role is not valid for this login flow"

    admin_on_player_response = client.post(
        "/auth/login",
        json={"email": admin_email, "password": admin_password},
    )
    assert admin_on_player_response.status_code == 403, admin_on_player_response.text
    assert admin_on_player_response.json()["error"]["message"] == "Role is not valid for this login flow"
