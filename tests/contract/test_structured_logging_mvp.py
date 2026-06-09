from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.errors import register_error_handlers
from app.api.request_context import REQUEST_ID_HEADER, request_id_middleware
from app.core.structured_logging import MAX_STRING_LENGTH, log_event, sanitize_log_details
from app.modules.platform.access_sessions import service as access_session_service


def _json_lines(output: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_redaction_policy_covers_exact_suffix_substring_and_camel_case_keys(
    capsys: pytest.CaptureFixture[str],
) -> None:
    sensitive_details = {
        "authorization": "Bearer raw-auth",
        "bearerToken": "raw-bearer",
        "authHeader": "raw-header",
        "api_key": "raw-api-key",
        "database_url": "postgresql://raw",
        "nested": {
            "credentials": {
                "pwd": "raw-password",
                "server_seed": "raw-seed",
            }
        }
    }
    sanitized, used_fallback = sanitize_log_details(sensitive_details)

    assert used_fallback is False
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["bearerToken"] == "[REDACTED]"
    assert sanitized["authHeader"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["database_url"] == "[REDACTED]"
    assert sanitized["nested"]["credentials"] == "[REDACTED]"

    log_event("error", "system.unhandled_exception", sensitive_details, job_id="job_redaction")
    output = capsys.readouterr().out
    assert "raw-seed" not in output
    assert "raw-password" not in output
    assert "raw-auth" not in output


def test_log_event_truncates_strings_depth_and_oversized_payload(capsys: pytest.CaptureFixture[str]) -> None:
    log_event(
        "info",
        "system.unhandled_exception",
        {
            "long_value": "x" * 300,
            "nested": {"a": {"b": {"c": {"d": "too deep"}}}},
        },
        job_id="job_truncation",
    )

    event = _json_lines(capsys.readouterr().out)[0]
    details = event["details"]
    assert len(details["long_value"]) == MAX_STRING_LENGTH
    assert details["long_value"].endswith("\u2026[truncated]")
    assert details["nested"]["a"]["b"]["c"] == {"...truncated...": True}

    log_event(
        "info",
        "system.unhandled_exception",
        {f"field_{index}": "x" * 300 for index in range(60)},
        job_id="job_payload",
    )

    events = _json_lines(capsys.readouterr().out)
    assert events[0]["event_name"] == "log.payload_truncated"
    assert events[0]["details"]["original_event_name"] == "system.unhandled_exception"
    assert events[1]["event_name"] == "system.unhandled_exception"
    assert "details" not in events[1]


def test_log_event_uses_request_id_or_job_id_context(capsys: pytest.CaptureFixture[str]) -> None:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)

    @app.get("/emit")
    def emit_log():
        log_event("error", "system.unhandled_exception", {"error_code": "CK.SYSTEM.INTERNAL_ERROR"})
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/emit", headers={REQUEST_ID_HEADER: "support_12345"})

    assert response.status_code == 200
    request_event = _json_lines(capsys.readouterr().out)[0]
    assert request_event["request_id"] == "support_12345"
    assert "job_id" not in request_event

    log_event("error", "access_session.timeout_sweep_failed", {"job_name": "sweep"}, job_id="job_123")
    job_event = _json_lines(capsys.readouterr().out)[0]
    assert job_event["job_id"] == "job_123"
    assert "request_id" not in job_event


def test_log_event_emits_json_lines_and_handles_non_serializable_values(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_event(
        "warning",
        "system.http_exception_normalized",
        {
            "decimal": Decimal("10.50"),
            "timestamp": datetime(2026, 5, 25, tzinfo=UTC),
            "roles": {"admin", "support"},
        },
        job_id="job_non_serializable",
    )

    events = _json_lines(capsys.readouterr().out)
    assert events[0]["event_name"] == "log.serialization_fallback"
    assert events[1]["event_name"] == "system.http_exception_normalized"
    assert events[1]["details"]["decimal"] == "10.50"
    assert "admin" in events[1]["details"]["roles"]


def test_log_event_without_request_or_job_uses_dash_and_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_event("info", "system.unhandled_exception", {"error_code": "CK.SYSTEM.INTERNAL_ERROR"})

    events = _json_lines(capsys.readouterr().out)
    assert events[0]["event_name"] == "log.missing_request_id"
    assert events[0]["request_id"] == "-"
    assert events[1]["event_name"] == "system.unhandled_exception"
    assert events[1]["request_id"] == "-"


class _DemoPayload(BaseModel):
    amount: int


def test_central_handlers_emit_structured_events_without_raw_secret(
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)
    register_error_handlers(app)

    @app.post("/validation")
    def validation(payload: _DemoPayload):
        return payload

    @app.get("/http-raw")
    def http_raw():
        raise HTTPException(status_code=400, detail="raw database token secret")

    @app.get("/unexpected")
    def unexpected():
        raise RuntimeError("raw stack secret")

    client = TestClient(app, raise_server_exceptions=False)

    validation_response = client.post("/validation", json={"amount": "bad"})
    http_response = client.get("/http-raw")
    unexpected_response = client.get("/unexpected", headers={REQUEST_ID_HEADER: "support_500"})

    assert validation_response.status_code == 422
    assert http_response.status_code == 400
    assert unexpected_response.status_code == 500
    assert unexpected_response.headers[REQUEST_ID_HEADER] == "support_500"
    assert unexpected_response.json()["error"]["support_id"] == "support_500"
    output = capsys.readouterr().out
    events = _json_lines(output)
    assert [event["event_name"] for event in events] == [
        "system.validation_error",
        "system.http_exception_normalized",
        "system.unhandled_exception",
    ]
    assert events[2]["request_id"] == "support_500"
    assert "raw database token secret" not in output
    assert "raw stack secret" not in output


def test_timeout_auto_settlement_failure_logs_critical_job_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_settlement(*, cursor, session):
        raise RuntimeError("settlement raw secret")

    monkeypatch.setattr(access_session_service, "_auto_settle_active_round_for_access_session", fail_settlement)

    with pytest.raises(RuntimeError):
        access_session_service._timeout_access_session(
            cursor=object(),
            session={
                "id": "access-session-1",
                "user_id": "user-1",
                "game_code": "mines",
                "title_code": "mines_classic",
                "site_code": "casinoking",
            },
            job_id="job_sweep",
        )

    event = _json_lines(capsys.readouterr().out)[0]
    assert event["level"] == "critical"
    assert event["event_name"] == "access_session.auto_settlement_failed"
    assert event["job_id"] == "job_sweep"
    assert "request_id" not in event
    assert event["details"]["access_session_id"] == "access-session-1"
    assert "settlement raw secret" not in json.dumps(event)
