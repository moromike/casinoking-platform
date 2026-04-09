"""
Integration tests for Admin RBAC (Role-Based Access Control).

Tests cover:
- Superadmin can access all areas (Finance, End-User, Mines)
- Admin with specific area can access that area only
- Admin without area gets 403 on protected endpoints
- GET /admin/auth/me returns correct profile
- POST /admin/admins creates new admin (superadmin only)
- PUT /admin/admins/{id}/profile updates admin profile (superadmin only)
"""
from __future__ import annotations

from uuid import uuid4

import httpx
import psycopg
from psycopg.rows import dict_row
import pytest

from app.modules.auth.service import ensure_local_admin
from app.db.connection import db_connection as _db_connection


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _create_admin_with_profile(
    *,
    prefix: str,
    is_superadmin: bool,
    areas: list[str],
    database_url: str,
) -> dict[str, object]:
    """Create an admin user via ensure_local_admin and set their admin_profiles row."""
    email = f"{prefix}-{uuid4().hex[:10]}@example.com"
    password = f"StrongPass-{uuid4().hex[:10]}"
    bootstrap = ensure_local_admin(email=email, password=password)
    user_id = bootstrap["user_id"]

    with psycopg.connect(database_url, row_factory=dict_row, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO admin_profiles (user_id, is_superadmin, areas)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                    SET is_superadmin = EXCLUDED.is_superadmin,
                        areas = EXCLUDED.areas
                """,
                (user_id, is_superadmin, areas),
            )

    return {
        "user_id": user_id,
        "email": email,
        "password": password,
    }


def _login_admin(client: httpx.Client, email: str, password: str) -> str:
    response = client.post(
        "/admin/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["data"]["access_token"]


# ─── GET /admin/auth/me ────────────────────────────────────────────────────────

def test_get_admin_me_returns_profile_for_superadmin(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="me-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["is_superadmin"] is True
    assert isinstance(data["areas"], list)
    assert data["email"] == admin["email"]
    assert data["role"] == "admin"


def test_get_admin_me_returns_profile_for_area_admin(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="me-area-admin",
        is_superadmin=False,
        areas=["finance", "end_user"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["is_superadmin"] is False
    assert set(data["areas"]) == {"finance", "end_user"}


def test_get_admin_me_requires_auth(client: httpx.Client) -> None:
    response = client.get("/admin/auth/me")
    assert response.status_code == 401


# ─── Finance area ──────────────────────────────────────────────────────────────

def test_superadmin_can_access_finance_ledger_report(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="finance-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/reports/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_finance_admin_can_access_ledger_report(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="finance-area",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/reports/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_non_finance_admin_gets_403_on_ledger_report(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="no-finance",
        is_superadmin=False,
        areas=["end_user"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/reports/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text


def test_admin_with_no_areas_gets_403_on_ledger_report(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="no-areas",
        is_superadmin=False,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/reports/ledger",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text


# ─── End-User area ─────────────────────────────────────────────────────────────

def test_superadmin_can_list_users(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="users-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_end_user_admin_can_list_users(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="end-user-area",
        is_superadmin=False,
        areas=["end_user"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_non_end_user_admin_gets_403_on_list_users(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="no-end-user",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text


# ─── Mines area ────────────────────────────────────────────────────────────────

def test_superadmin_can_access_mines_backoffice_config(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="mines-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/games/mines/backoffice-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_mines_admin_can_access_mines_backoffice_config(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="mines-area",
        is_superadmin=False,
        areas=["mines"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/games/mines/backoffice-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


def test_non_mines_admin_gets_403_on_mines_backoffice_config(
    client: httpx.Client,
    database_url: str,
) -> None:
    admin = _create_admin_with_profile(
        prefix="no-mines",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    token = _login_admin(client, admin["email"], admin["password"])

    response = client.get(
        "/admin/games/mines/backoffice-config",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text


# ─── Admin management (superadmin only) ────────────────────────────────────────

def test_superadmin_can_create_new_admin(
    client: httpx.Client,
    database_url: str,
) -> None:
    superadmin = _create_admin_with_profile(
        prefix="creator-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, superadmin["email"], superadmin["password"])

    new_email = f"new-admin-{uuid4().hex[:10]}@example.com"
    response = client.post(
        "/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": new_email,
            "password": "StrongPass-newadmin",
            "is_superadmin": False,
            "areas": ["finance", "end_user"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["email"] == new_email
    assert data["role"] == "admin"
    assert data["is_superadmin"] is False
    assert set(data["areas"]) == {"finance", "end_user"}


def test_non_superadmin_cannot_create_admin(
    client: httpx.Client,
    database_url: str,
) -> None:
    area_admin = _create_admin_with_profile(
        prefix="area-admin-no-create",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    token = _login_admin(client, area_admin["email"], area_admin["password"])

    response = client.post(
        "/admin/admins",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": f"blocked-{uuid4().hex[:8]}@example.com",
            "password": "StrongPass-blocked",
            "is_superadmin": False,
            "areas": ["finance"],
        },
    )
    assert response.status_code == 403, response.text


def test_superadmin_can_update_admin_profile(
    client: httpx.Client,
    database_url: str,
) -> None:
    superadmin = _create_admin_with_profile(
        prefix="updater-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    target_admin = _create_admin_with_profile(
        prefix="target-to-update",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    token = _login_admin(client, superadmin["email"], superadmin["password"])

    response = client.put(
        f"/admin/admins/{target_admin['user_id']}/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "is_superadmin": False,
            "areas": ["mines", "end_user"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert set(data["areas"]) == {"mines", "end_user"}
    assert data["is_superadmin"] is False


def test_non_superadmin_cannot_update_admin_profile(
    client: httpx.Client,
    database_url: str,
) -> None:
    area_admin = _create_admin_with_profile(
        prefix="area-admin-no-update",
        is_superadmin=False,
        areas=["finance"],
        database_url=database_url,
    )
    target_admin = _create_admin_with_profile(
        prefix="target-no-update",
        is_superadmin=False,
        areas=["mines"],
        database_url=database_url,
    )
    token = _login_admin(client, area_admin["email"], area_admin["password"])

    response = client.put(
        f"/admin/admins/{target_admin['user_id']}/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "is_superadmin": True,
            "areas": [],
        },
    )
    assert response.status_code == 403, response.text


# ─── list_users includes is_superadmin and areas ──────────────────────────────

def test_list_users_includes_admin_profile_fields(
    client: httpx.Client,
    database_url: str,
) -> None:
    superadmin = _create_admin_with_profile(
        prefix="list-users-superadmin",
        is_superadmin=True,
        areas=[],
        database_url=database_url,
    )
    token = _login_admin(client, superadmin["email"], superadmin["password"])

    response = client.get(
        f"/admin/users?email={superadmin['email']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    users = response.json()["data"]
    assert len(users) >= 1
    # Find the superadmin in the list
    found = next((u for u in users if u["email"] == superadmin["email"]), None)
    assert found is not None
    assert "is_superadmin" in found
    assert "areas" in found
