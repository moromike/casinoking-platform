from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.errors import AppError, register_error_handlers
from app.api.request_context import REQUEST_ID_HEADER, REQUEST_ID_PATTERN, request_id_middleware
from app.api.responses import error_response


class DemoPayload(BaseModel):
    amount: int


def _build_client() -> TestClient:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)
    register_error_handlers(app)

    @app.get("/legacy-error-response")
    def legacy_error_response():
        return error_response(
            status_code=401,
            code="UNAUTHORIZED",
            message="Invalid bearer token",
        )

    @app.get("/app-error")
    def app_error():
        raise AppError("CK.AUTH.SESSION_EXPIRED")

    @app.get("/http-envelope")
    def http_envelope():
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": {"code": "X.LEGACY", "message": "Legacy"}},
        )

    @app.get("/http-raw")
    def http_raw():
        raise HTTPException(status_code=400, detail="raw database token secret")

    @app.get("/http-dict")
    def http_dict():
        raise HTTPException(status_code=400, detail={"field_x": "value", "field": "amount"})

    @app.get("/http-envelope-extra")
    def http_envelope_extra():
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {
                    "code": "X.EXTRA",
                    "message": "Extra",
                    "details": {"field": "bet_amount", "secret": "nope"},
                },
                "extra": "leak",
            },
        )

    @app.post("/validation")
    def validation(payload: DemoPayload):
        return payload

    @app.get("/unexpected")
    def unexpected():
        raise RuntimeError("raw stack secret")

    return TestClient(app, raise_server_exceptions=False)


def test_request_id_generated_and_legacy_error_response_gets_support_fields() -> None:
    client = _build_client()
    response = client.get("/legacy-error-response")

    assert response.status_code == 401
    request_id = response.headers[REQUEST_ID_HEADER]
    assert REQUEST_ID_PATTERN.fullmatch(request_id)
    error = response.json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert error["support_id"] == request_id
    assert error["request_id"] == request_id
    assert error["retryable"] is True


def test_valid_request_id_is_preserved_and_invalid_request_id_is_rejected() -> None:
    client = _build_client()

    valid_response = client.get("/app-error", headers={REQUEST_ID_HEADER: "support_12345"})
    assert valid_response.headers[REQUEST_ID_HEADER] == "support_12345"
    assert valid_response.json()["error"]["support_id"] == "support_12345"

    invalid_response = client.get("/app-error", headers={REQUEST_ID_HEADER: "bad\nid"})
    replacement = invalid_response.headers[REQUEST_ID_HEADER]
    assert replacement != "bad\nid"
    assert REQUEST_ID_PATTERN.fullmatch(replacement)


def test_app_error_uses_registry_definition() -> None:
    client = _build_client()
    response = client.get("/app-error")

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "CK.AUTH.SESSION_EXPIRED"
    assert error["message"] == "Sessione scaduta, ricarica."
    assert error["retryable"] is True


def test_http_exception_existing_envelope_is_normalized_not_nested() -> None:
    client = _build_client()
    response = client.get("/http-envelope")

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert "detail" not in payload
    error = payload["error"]
    assert error["code"] == "X.LEGACY"
    assert error["message"] == "Legacy"
    assert error["support_id"]


def test_http_exception_raw_string_maps_to_safe_message() -> None:
    client = _build_client()
    response = client.get("/http-raw")

    error = response.json()["error"]
    assert error["code"] == "CK.VALIDATION.INVALID_REQUEST"
    assert error["message"] == "Richiesta non valida."
    assert "raw database token secret" not in response.text


def test_http_exception_dict_uses_safe_detail_whitelist() -> None:
    client = _build_client()
    response = client.get("/http-dict")

    details = response.json()["error"]["details"]
    assert details == {"field": "amount"}
    assert "field_x" not in response.text


def test_http_exception_envelope_extra_fields_are_ignored() -> None:
    client = _build_client()
    response = client.get("/http-envelope-extra")

    error = response.json()["error"]
    assert error["code"] == "X.EXTRA"
    assert error["details"] == {"field": "bet_amount"}
    assert "extra" not in response.text
    assert "nope" not in response.text


def test_validation_and_unexpected_errors_use_platform_codes_without_raw_leak() -> None:
    client = _build_client()

    validation_response = client.post("/validation", json={"amount": "bad"})
    assert validation_response.status_code == 422
    assert validation_response.json()["error"]["code"] == "CK.VALIDATION.INVALID_REQUEST"

    unexpected_response = client.get("/unexpected")
    assert unexpected_response.status_code == 500
    error = unexpected_response.json()["error"]
    assert error["code"] == "CK.SYSTEM.INTERNAL_ERROR"
    assert "raw stack secret" not in unexpected_response.text
