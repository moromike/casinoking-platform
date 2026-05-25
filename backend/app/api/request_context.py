from __future__ import annotations

from contextvars import ContextVar
import logging
import re
from uuid import uuid4

from starlette.requests import Request


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    return f"req_{uuid4().hex}"


def is_valid_request_id(value: str | None) -> bool:
    if value is None:
        return False
    return bool(REQUEST_ID_PATTERN.fullmatch(value))


def resolve_request_id(inbound_request_id: str | None) -> str:
    if is_valid_request_id(inbound_request_id):
        return str(inbound_request_id)
    if inbound_request_id:
        logger.info("input request id rejected")
    return generate_request_id()


def get_request_id() -> str | None:
    return _request_id_var.get()


def get_or_create_request_id() -> str:
    current = get_request_id()
    if current:
        return current
    request_id = generate_request_id()
    _request_id_var.set(request_id)
    return request_id


async def request_id_middleware(request: Request, call_next):
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    token = _request_id_var.set(request_id)
    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        _request_id_var.reset(token)
