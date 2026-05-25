from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import platform_settings as platform_settings_route
from app.modules.platform.settings import service as settings_service
from app.modules.platform.settings.service import (
    GAP_RISKS,
    SETTINGS_DESCRIPTORS,
    build_platform_settings_inventory,
    validate_descriptor_contract,
)


ROOT = Path(__file__).resolve().parents[2]
SECRET_SENTINELS = (
    "postgresql://secret-user:secret-pass@db.example:5432/prod",
    "redis://:secret-redis@redis.example:6379/0",
    "jwt-secret-sentinel",
    "site-password-sentinel",
    "mines-seed-sentinel",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_descriptor_contract_has_required_fields_and_no_editable_rows() -> None:
    validate_descriptor_contract()

    assert len(SETTINGS_DESCRIPTORS) >= 28
    keys = {descriptor.key for descriptor in SETTINGS_DESCRIPTORS}
    for expected_key in {
        "database.url",
        "jwt.secret",
        "site_access.password",
        "site_access.client_default",
        "health.ready_db_redis",
        "auth.rbac_fallback",
        "cms_v2_lab.admin_token_in_query",
        "game_registry.backends",
        "error_registry.status",
    }:
        assert expected_key in keys

    for descriptor in SETTINGS_DESCRIPTORS:
        assert descriptor.key
        assert descriptor.label
        assert descriptor.source_of_truth
        assert descriptor.owner
        assert descriptor.visibility in {"hidden", "masked", "read_only", "editable_future"}
        assert descriptor.risk_class in {"low", "medium", "high", "critical"}
        assert descriptor.environment_scope
        assert descriptor.restart_required in {"yes", "no", "unknown"}
        assert descriptor.audit_required in {"yes", "no", "future"}
        assert descriptor.editable_now is False
        assert descriptor.masking_rule
        assert descriptor.evidence
        if descriptor.visibility == "editable_future":
            assert descriptor.editable_when


def test_inventory_payload_masks_hidden_values_and_does_not_leak_secrets(monkeypatch) -> None:
    monkeypatch.setattr(
        settings_service,
        "settings",
        SimpleNamespace(
            app_name="CasinoKing Test",
            app_version="9.9.9",
            app_env="test",
            api_v1_prefix="/api/v1",
            database_url=SECRET_SENTINELS[0],
            redis_url=SECRET_SENTINELS[1],
            jwt_secret=SECRET_SENTINELS[2],
            jwt_access_token_ttl_minutes=60,
            game_launch_token_ttl_minutes=5,
            site_access_password=SECRET_SENTINELS[3],
            mines_server_seed=SECRET_SENTINELS[4],
            cors_allowed_origins=("https://one.example", "https://two.example"),
            asset_storage_root=Path("/very/secret/path/assets"),
            asset_public_base_url="/static/games",
        ),
    )

    payload = build_platform_settings_inventory()
    payload_text = str(payload)

    for sentinel in SECRET_SENTINELS:
        assert sentinel not in payload_text

    rows = {row["key"]: row for row in payload["inventory"]}
    for key in ["database.url", "redis.url", "jwt.secret", "site_access.password", "mines.server_seed"]:
        row = rows[key]
        assert row["visibility"] == "hidden"
        assert row["state"] == {"status": row["status"], "configured": True}

    cors_row = rows["cors.allowed_origins"]
    assert cors_row["visibility"] == "masked"
    assert cors_row["state"]["display_value"] == "2 entries configured"
    assert "https://one.example" not in payload_text


def test_gap_risk_writeups_are_present_with_follow_up_wp() -> None:
    payload = build_platform_settings_inventory()
    gap_keys = {gap["key"] for gap in payload["gap_risks"]}
    descriptor_rows = {row["key"]: row for row in payload["inventory"]}

    assert gap_keys == {gap.key for gap in GAP_RISKS}
    for key in {
        "site_access.client_default",
        "health.ready_db_redis",
        "auth.rbac_fallback",
        "cms_v2_lab.admin_token_in_query",
    }:
        assert descriptor_rows[key]["status"] == "gap"
        matching_gap = next(gap for gap in payload["gap_risks"] if gap["key"] == key)
        assert matching_gap["follow_up_wp"].startswith("WP-")
        assert matching_gap["impact"]
        assert matching_gap["mvp_mitigation"]
        assert matching_gap["long_term_mitigation"]


def test_game_registry_health_uses_backend_source_of_truth_and_pending_when_needed() -> None:
    payload = build_platform_settings_inventory()
    health_rows = payload["game_registry_health"]

    assert {row["game_code"] for row in health_rows} == {"mines", "boxe", "hi_lo"}
    for row in health_rows:
        assert row["source_of_truth"] == "backend/app/modules/platform/game_codes.py"
        assert row["checks"]["backend"]["status"] == "present"
        assert row["checks"]["frontend_player_registry"]["status"] in {"present", "pending", "gap"}
        assert row["checks"]["title_editor_registry"]["status"] in {"present", "pending", "gap"}
        assert row["checks"]["finance_replay_descriptor"]["status"] in {"present", "pending", "gap"}
        assert row["checks"]["error_namespace"]["status"] in {"present", "pending"}
        assert row["checks"]["smoke_status"]["status"] == "pending"


def test_error_matrix_exposes_ck_registry_read_only() -> None:
    payload = build_platform_settings_inventory()
    error_matrix = payload["error_matrix"]
    codes = {row["code"] for row in error_matrix["codes"]}

    assert error_matrix["status"] == "available"
    assert "CK.AUTH.FORBIDDEN" in codes
    assert "CK.SYSTEM.INTERNAL_ERROR" in codes
    for row in error_matrix["codes"]:
        assert row["code"].startswith("CK.")
        assert set(row) == {"code", "http_status", "message", "retryable", "log_level"}


def test_platform_settings_endpoint_requires_explicit_superadmin_profile(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(platform_settings_route.router)
    app.dependency_overrides[platform_settings_route.get_current_user] = lambda: {
        "id": "admin-without-profile",
        "email": "admin@example.com",
        "role": "admin",
        "status": "active",
    }
    monkeypatch.setattr(platform_settings_route, "get_admin_profile", lambda user_id: None)

    response = TestClient(app).get("/admin/platform-settings")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CK.AUTH.FORBIDDEN"


def test_platform_settings_endpoint_allows_explicit_superadmin_profile(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(platform_settings_route.router)
    app.dependency_overrides[platform_settings_route.get_current_user] = lambda: {
        "id": "explicit-superadmin",
        "email": "superadmin@example.com",
        "role": "admin",
        "status": "active",
    }
    monkeypatch.setattr(
        platform_settings_route,
        "get_admin_profile",
        lambda user_id: {"user_id": user_id, "is_superadmin": True, "areas": []},
    )

    response = TestClient(app).get("/admin/platform-settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["editable_now_count"] == 0


def test_frontend_platform_settings_panel_is_read_only() -> None:
    panel_source = _read("frontend/app/ui/admin-platform-settings-panel.tsx")
    console_source = _read("frontend/app/ui/casinoking-console.tsx")
    shell_source = _read("frontend/app/ui/admin-shell-panel.tsx")

    forbidden_fragments = [
        "<input",
        "<select",
        "<textarea",
        'type="submit"',
        "Save draft",
        "Publish live",
        "onChange",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in panel_source

    assert 'apiRequest<PlatformSettingsInventory>("/admin/platform-settings"' in panel_source
    assert "Platform Settings" in shell_source
    assert 'adminSection === "platform_settings" && isSuperadmin' in console_source
