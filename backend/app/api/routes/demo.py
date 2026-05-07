from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Request, status
import jwt
from pydantic import BaseModel

from app.api.responses import error_response
from app.core.config import settings
from app.modules.platform.game_launch.service import (
    GAME_CODE_MINES,
    SITE_CODE_CASINOKING,
    GameLaunchTokenValidationError,
    issue_demo_game_launch_token,
    validate_admin_game_preview_token,
)

router = APIRouter(prefix="/demo", tags=["demo"])

DEMO_ANON_TOKEN_KIND = "demo_anon"
DEMO_ANON_ISSUER = "casinoking-platform"
DEMO_ANON_AUDIENCE = "casinoking-demo"
DEMO_ANON_TOKEN_TTL_DAYS = 30
DEMO_TOKEN_RATE_LIMIT = 10
DEMO_TOKEN_RATE_WINDOW_SECONDS = 60

_token_requests_by_ip: dict[str, deque[datetime]] = defaultdict(deque)


class DemoLaunchRequest(BaseModel):
    title_code: str | None = None
    site_code: str | None = None
    game_code: str | None = None
    preview_token: str | None = None


@router.post("/token")
def issue_demo_token(
    request: Request,
    x_forwarded_for: str | None = Header(default=None, alias="X-Forwarded-For"),
) -> dict[str, object] | object:
    client_ip = _resolve_client_ip(request=request, x_forwarded_for=x_forwarded_for)
    if _is_rate_limited(client_ip):
        return error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMITED",
            message="Too many demo token requests",
        )

    now = datetime.now(UTC)
    anonymous_id = str(uuid4())
    payload = {
        "iss": DEMO_ANON_ISSUER,
        "aud": DEMO_ANON_AUDIENCE,
        "sub": anonymous_id,
        "kind": DEMO_ANON_TOKEN_KIND,
        "iat": now,
        "exp": now + timedelta(days=DEMO_ANON_TOKEN_TTL_DAYS),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return {
        "success": True,
        "data": {
            "anonymous_token": token,
        },
    }


@router.post("/launch")
def issue_demo_launch(
    payload: DemoLaunchRequest,
    demo_token: str | None = Header(default=None, alias="X-Demo-Token"),
) -> dict[str, object] | object:
    if not demo_token:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="X-Demo-Token header is required",
        )

    try:
        anonymous_id = _validate_demo_token(demo_token)
        allow_unpublished_preview = False
        preview_admin_user_id: str | None = None
        game_code = payload.game_code or GAME_CODE_MINES
        title_code = payload.title_code
        site_code = payload.site_code or SITE_CODE_CASINOKING

        if payload.preview_token:
            preview_context = validate_admin_game_preview_token(
                preview_token=payload.preview_token,
            )
            _ensure_preview_payload_matches(
                requested_game_code=payload.game_code,
                requested_title_code=payload.title_code,
                requested_site_code=payload.site_code,
                preview_context=preview_context,
            )
            allow_unpublished_preview = True
            preview_admin_user_id = str(preview_context["admin_user_id"])
            game_code = str(preview_context["game_code"])
            title_code = str(preview_context["title_code"])
            site_code = str(preview_context["site_code"])

        result = issue_demo_game_launch_token(
            anonymous_id=anonymous_id,
            game_code=game_code,
            title_code=title_code,
            site_code=site_code,
            allow_unpublished_preview=allow_unpublished_preview,
            preview_admin_user_id=preview_admin_user_id,
        )
    except DemoTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except GameLaunchTokenValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code,
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


class DemoTokenValidationError(Exception):
    pass


def _validate_demo_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=DEMO_ANON_AUDIENCE,
            issuer=DEMO_ANON_ISSUER,
        )
    except jwt.InvalidTokenError as exc:
        raise DemoTokenValidationError("Demo token is not valid") from exc

    if payload.get("kind") != DEMO_ANON_TOKEN_KIND:
        raise DemoTokenValidationError("Demo token is not valid")
    anonymous_id = payload.get("sub")
    if not isinstance(anonymous_id, str) or not anonymous_id:
        raise DemoTokenValidationError("Demo token is not valid")
    try:
        UUID(anonymous_id)
    except ValueError as exc:
        raise DemoTokenValidationError("Demo token is not valid") from exc
    return anonymous_id


def _ensure_preview_payload_matches(
    *,
    requested_game_code: str | None,
    requested_title_code: str | None,
    requested_site_code: str | None,
    preview_context: dict[str, object],
) -> None:
    comparisons = [
        (requested_game_code, preview_context["game_code"], "game code"),
        (requested_title_code, preview_context["title_code"], "title code"),
        (requested_site_code, preview_context["site_code"], "site code"),
    ]
    for requested, expected, label in comparisons:
        if requested is None:
            continue
        if _normalize_requested_value(requested) != _normalize_requested_value(str(expected)):
            raise GameLaunchTokenValidationError(
                f"Admin preview token {label} does not match the launch request"
            )


def _normalize_requested_value(value: str) -> str:
    return value.strip().lower()


def _is_rate_limited(client_ip: str) -> bool:
    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=DEMO_TOKEN_RATE_WINDOW_SECONDS)
    requests = _token_requests_by_ip[client_ip]
    while requests and requests[0] < window_start:
        requests.popleft()
    if len(requests) >= DEMO_TOKEN_RATE_LIMIT:
        return True
    requests.append(now)
    return False


def _resolve_client_ip(*, request: Request, x_forwarded_for: str | None) -> str:
    if x_forwarded_for:
        return x_forwarded_for.split(",", maxsplit=1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"
