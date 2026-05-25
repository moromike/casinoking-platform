from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.api.request_context import REQUEST_ID_HEADER, get_or_create_request_id


logger = logging.getLogger(__name__)
HTTP_422_UNPROCESSABLE_ENTITY = 422


@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    http_status: int
    message: str
    retryable: bool
    log_level: str = "warning"


ERROR_REGISTRY: dict[str, ErrorDefinition] = {
    "CK.AUTH.UNAUTHORIZED": ErrorDefinition(
        code="CK.AUTH.UNAUTHORIZED",
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Autenticazione richiesta.",
        retryable=True,
    ),
    "CK.AUTH.INVALID_TOKEN": ErrorDefinition(
        code="CK.AUTH.INVALID_TOKEN",
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Sessione scaduta, ricarica.",
        retryable=True,
    ),
    "CK.AUTH.SESSION_EXPIRED": ErrorDefinition(
        code="CK.AUTH.SESSION_EXPIRED",
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Sessione scaduta, ricarica.",
        retryable=True,
    ),
    "CK.AUTH.FORBIDDEN": ErrorDefinition(
        code="CK.AUTH.FORBIDDEN",
        http_status=status.HTTP_403_FORBIDDEN,
        message="Operazione non autorizzata.",
        retryable=False,
    ),
    "CK.VALIDATION.INVALID_REQUEST": ErrorDefinition(
        code="CK.VALIDATION.INVALID_REQUEST",
        http_status=HTTP_422_UNPROCESSABLE_ENTITY,
        message="Richiesta non valida.",
        retryable=False,
    ),
    "CK.WALLET.INSUFFICIENT_BALANCE": ErrorDefinition(
        code="CK.WALLET.INSUFFICIENT_BALANCE",
        http_status=HTTP_422_UNPROCESSABLE_ENTITY,
        message="Saldo insufficiente.",
        retryable=False,
    ),
    "CK.LEDGER.IDEMPOTENCY_KEY_REQUIRED": ErrorDefinition(
        code="CK.LEDGER.IDEMPOTENCY_KEY_REQUIRED",
        http_status=HTTP_422_UNPROCESSABLE_ENTITY,
        message="Chiave idempotenza richiesta.",
        retryable=False,
    ),
    "CK.LEDGER.IDEMPOTENCY_CONFLICT": ErrorDefinition(
        code="CK.LEDGER.IDEMPOTENCY_CONFLICT",
        http_status=status.HTTP_409_CONFLICT,
        message="Operazione gia' registrata con parametri diversi.",
        retryable=False,
    ),
    "CK.GAME.LAUNCH_TOKEN_REQUIRED": ErrorDefinition(
        code="CK.GAME.LAUNCH_TOKEN_REQUIRED",
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Sessione gioco scaduta, ricarica.",
        retryable=True,
    ),
    "CK.GAME.LAUNCH_TOKEN_INVALID": ErrorDefinition(
        code="CK.GAME.LAUNCH_TOKEN_INVALID",
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Sessione gioco scaduta, ricarica.",
        retryable=True,
    ),
    "CK.GAME.ROUND_CLOSED": ErrorDefinition(
        code="CK.GAME.ROUND_CLOSED",
        http_status=status.HTTP_409_CONFLICT,
        message="Round gia' concluso.",
        retryable=False,
    ),
    "CK.SYSTEM.SERVICE_UNAVAILABLE": ErrorDefinition(
        code="CK.SYSTEM.SERVICE_UNAVAILABLE",
        http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Servizio temporaneamente non disponibile.",
        retryable=True,
        log_level="error",
    ),
    "CK.SYSTEM.INTERNAL_ERROR": ErrorDefinition(
        code="CK.SYSTEM.INTERNAL_ERROR",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Servizio temporaneamente non disponibile.",
        retryable=True,
        log_level="error",
    ),
}

LEGACY_ERROR_ALIASES: dict[str, str] = {
    "UNAUTHORIZED": "CK.AUTH.UNAUTHORIZED",
    "FORBIDDEN": "CK.AUTH.FORBIDDEN",
    "VALIDATION_ERROR": "CK.VALIDATION.INVALID_REQUEST",
    "INSUFFICIENT_BALANCE": "CK.WALLET.INSUFFICIENT_BALANCE",
    "IDEMPOTENCY_KEY_REQUIRED": "CK.LEDGER.IDEMPOTENCY_KEY_REQUIRED",
    "IDEMPOTENCY_CONFLICT": "CK.LEDGER.IDEMPOTENCY_CONFLICT",
    "GAME_LAUNCH_TOKEN_REQUIRED": "CK.GAME.LAUNCH_TOKEN_REQUIRED",
    "GAME_LAUNCH_TOKEN_INVALID": "CK.GAME.LAUNCH_TOKEN_INVALID",
    "ROUND_CLOSED": "CK.GAME.ROUND_CLOSED",
    "ROUND_ALREADY_CLOSED": "CK.GAME.ROUND_CLOSED",
}

SAFE_DETAIL_KEYS = {
    "field",
    "fields",
    "loc",
    "type",
    "reason",
    "limit",
    "minimum",
    "maximum",
}


class AppError(Exception):
    def __init__(
        self,
        code: str,
        *,
        message: str | None = None,
        status_code: int | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def lookup_error_definition(code: str) -> ErrorDefinition | None:
    return ERROR_REGISTRY.get(LEGACY_ERROR_ALIASES.get(code, code))


def build_error_payload(
    *,
    code: str,
    message: str | None = None,
    status_code: int | None = None,
    details: dict[str, object] | None = None,
    retryable: bool | None = None,
) -> dict[str, object]:
    request_id = get_or_create_request_id()
    definition = lookup_error_definition(code)
    resolved_code = code
    resolved_message = message or definition.message if definition else message or "Errore applicativo."
    resolved_retryable = retryable if retryable is not None else (definition.retryable if definition else False)

    error: dict[str, object] = {
        "code": resolved_code,
        "message": resolved_message,
        "support_id": request_id,
        "request_id": request_id,
        "retryable": resolved_retryable,
    }
    if details:
        error["details"] = sanitize_details(details)
    return {"success": False, "error": error}


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str | None = None,
    details: dict[str, object] | None = None,
    retryable: bool | None = None,
) -> JSONResponse:
    request_id = get_or_create_request_id()
    payload = build_error_payload(
        code=code,
        message=message,
        status_code=status_code,
        details=details,
        retryable=retryable,
    )
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers={REQUEST_ID_HEADER: request_id},
    )


def normalize_http_exception_detail(
    *,
    status_code: int,
    detail: Any,
) -> tuple[str, str | None, dict[str, object] | None, bool | None]:
    if _looks_like_error_envelope(detail):
        error = detail["error"]
        code = str(error.get("code") or _code_for_status(status_code))
        message = str(error["message"]) if isinstance(error.get("message"), str) else None
        details = sanitize_details(error.get("details")) if isinstance(error.get("details"), dict) else None
        retryable = error.get("retryable") if isinstance(error.get("retryable"), bool) else None
        return code, message, details, retryable

    if isinstance(detail, dict):
        return _code_for_status(status_code), None, sanitize_details(detail), None

    return _code_for_status(status_code), None, None, None


def sanitize_details(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    sanitized: dict[str, object] = {}
    for key, raw_value in value.items():
        if key not in SAFE_DETAIL_KEYS:
            continue
        sanitized[key] = _safe_detail_value(raw_value)
    return sanitized


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request, exc: AppError) -> JSONResponse:
        definition = lookup_error_definition(exc.code)
        status_code = exc.status_code or (definition.http_status if definition else status.HTTP_400_BAD_REQUEST)
        return build_error_response(
            status_code=status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request, exc: RequestValidationError) -> JSONResponse:
        return build_error_response(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            code="CK.VALIDATION.INVALID_REQUEST",
            details={"fields": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
        code, message, details, retryable = normalize_http_exception_detail(
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return build_error_response(
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details,
            retryable=retryable,
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(_request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API exception", exc_info=exc)
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="CK.SYSTEM.INTERNAL_ERROR",
        )


def _looks_like_error_envelope(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("success") is False
        and isinstance(value.get("error"), dict)
    )


def _code_for_status(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "CK.AUTH.UNAUTHORIZED"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "CK.AUTH.FORBIDDEN"
    if status_code == HTTP_422_UNPROCESSABLE_ENTITY:
        return "CK.VALIDATION.INVALID_REQUEST"
    if status_code == status.HTTP_409_CONFLICT:
        return "CK.LEDGER.IDEMPOTENCY_CONFLICT"
    if status_code >= 500:
        return "CK.SYSTEM.SERVICE_UNAVAILABLE"
    return "CK.VALIDATION.INVALID_REQUEST"


def _safe_detail_value(value: Any) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_safe_detail_value(item) for item in value[:20]]
    if isinstance(value, dict):
        return {
            str(key): _safe_detail_value(nested_value)
            for key, nested_value in list(value.items())[:20]
            if isinstance(key, str)
        }
    return str(value)
