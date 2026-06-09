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
from app.modules.platform.game_runtime_descriptors import GAME_RUNTIME_DESCRIPTORS


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
        "mines.runtime_descriptor",
        "boxe.runtime_descriptor",
        "hi_lo.runtime_descriptor",
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

    payload = build_platform_settings_inventory()
    for row in payload["inventory"]:
        assert row["explanation"]["it"]
        assert row["explanation"]["en"]


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


def test_security_gap_writeups_are_marked_closed_with_follow_up_wp() -> None:
    payload = build_platform_settings_inventory()
    gap_keys = {gap["key"] for gap in payload["gap_risks"]}
    descriptor_rows = {row["key"]: row for row in payload["inventory"]}

    assert payload["summary"]["gap_count"] == 0
    assert gap_keys == {gap.key for gap in GAP_RISKS}
    for key in {
        "site_access.client_default",
        "health.ready_db_redis",
        "auth.rbac_fallback",
        "cms_v2_lab.admin_token_in_query",
    }:
        assert descriptor_rows[key]["status"] == "ok"
        matching_gap = next(gap for gap in payload["gap_risks"] if gap["key"] == key)
        assert matching_gap["follow_up_wp"].startswith("WP-")
        assert matching_gap["impact"]
        assert matching_gap["impact_it"]
        assert matching_gap["mvp_mitigation"].startswith("Closed:")
        assert matching_gap["mvp_mitigation_it"].startswith("Chiuso:")
        assert matching_gap["long_term_mitigation"]
        assert matching_gap["long_term_mitigation_it"]


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


def test_game_runtime_descriptors_are_uniform_and_hashed() -> None:
    payload = build_platform_settings_inventory()
    rows = {row["key"]: row for row in payload["inventory"]}

    assert set(GAME_RUNTIME_DESCRIPTORS) == {"mines", "boxe", "hi_lo"}
    assert {item["game_code"] for item in payload["game_runtime_descriptors"]} == {
        "mines",
        "boxe",
        "hi_lo",
    }
    for game_code, descriptor in GAME_RUNTIME_DESCRIPTORS.items():
        row = rows[f"{game_code}.runtime_descriptor"]
        assert row["source_of_truth"] == "registry"
        assert row["state"]["display_value"].startswith("runtime descriptor v1:")
        assert row["state"]["display_value"] != descriptor.payout_runtime_source
        assert row["notes"]

        payload_descriptor = next(
            item
            for item in payload["game_runtime_descriptors"]
            if item["game_code"] == game_code
        )
        assert payload_descriptor["payout_runtime_source"] == descriptor.payout_runtime_source
        assert payload_descriptor["math_source"] == descriptor.math_source
        assert payload_descriptor["rtp_source"] == descriptor.rtp_source
        assert payload_descriptor["replay_verification_source"] == descriptor.replay_verification_source
        assert payload_descriptor["spec_files"]
        for spec_file in payload_descriptor["spec_files"]:
            assert len(spec_file["sha256"]) == 64
            assert spec_file["path"] in descriptor.spec_paths


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


def test_admin_dependency_rejects_missing_admin_profile(monkeypatch) -> None:
    from fastapi import Depends

    from app.api import dependencies

    app = FastAPI()

    @app.get("/admin-probe")
    def admin_probe(
        current_admin: dict[str, object] | object = Depends(dependencies.get_current_admin),
    ) -> dict[str, object] | object:
        if not isinstance(current_admin, dict):
            return current_admin
        return {"success": True, "data": current_admin}

    monkeypatch.setattr(
        dependencies,
        "get_current_user",
        lambda authorization=None: {
            "id": "admin-without-profile",
            "email": "admin@example.com",
            "role": "admin",
            "status": "active",
        },
    )
    monkeypatch.setattr(dependencies, "get_admin_profile", lambda user_id: None)

    response = TestClient(app).get("/admin-probe")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CK.AUTH.FORBIDDEN"


def test_frontend_platform_settings_panel_is_read_only() -> None:
    panel_source = _read("frontend-v3/app/ui/admin-platform-settings-panel.tsx")
    console_source = _read("frontend-v3/app/ui/casinoking-console.tsx")
    shell_source = _read("frontend-v3/app/ui/admin-shell-panel.tsx")

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
    assert "STATUS_FILTERS" in panel_source
    assert "RISK_FILTERS" in panel_source
    assert "VISIBILITY_FILTERS" in panel_source
    assert "CATEGORY_DESCRIPTIONS" in panel_source
    assert "aria-expanded" in panel_source
    assert "Spiegazione" in panel_source
    assert "impact_it" in panel_source
    assert "Platform Settings" in shell_source
    assert "?token=" not in shell_source
    assert "ADMIN_STORAGE_KEYS" not in shell_source
    assert 'adminSection === "platform_settings" && isSuperadmin' in console_source
