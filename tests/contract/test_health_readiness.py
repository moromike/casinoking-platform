from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import health


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(health.router)
    return TestClient(app)


def test_ready_reports_ready_only_when_app_db_and_redis_are_ok(monkeypatch) -> None:
    monkeypatch.setattr(health, "_check_database", lambda: "ok")
    monkeypatch.setattr(health, "_check_redis", lambda: "ok")

    response = _client().get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["checks"] == {
        "app": "ok",
        "database": "ok",
        "redis": "ok",
    }


def test_ready_returns_503_when_dependency_is_down(monkeypatch) -> None:
    monkeypatch.setattr(health, "_check_database", lambda: "ok")
    monkeypatch.setattr(health, "_check_redis", lambda: "error")

    response = _client().get("/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["status"] == "not_ready"
    assert payload["data"]["checks"]["redis"] == "error"
