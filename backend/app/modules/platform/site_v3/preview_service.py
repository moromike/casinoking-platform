from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.api.errors import AppError
from app.core.config import settings
from app.db.connection import db_connection
from app.modules.platform.site_v3 import repository
from app.modules.platform.site_v3.service import (
    _normalize_code,
    _normalize_locale,
    _normalize_uuid,
    _record_page_audit,
    _require_site,
    build_snapshot_from_modules,
)


TOKEN_TYPE = "site_v3_draft_preview"
TOKEN_TTL_MINUTES = 15


def issue_draft_preview_token(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    admin_user_id: str,
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    normalized_admin_user_id = _normalize_uuid(admin_user_id, "Admin user id is invalid")

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
            )
            if page is None:
                raise AppError("SITEV3.PREVIEW.PAGE_NOT_FOUND")

            now = datetime.now(UTC)
            expires_at = now + timedelta(minutes=TOKEN_TTL_MINUTES)
            payload = {
                "typ": TOKEN_TYPE,
                "site_code": normalized_site_code,
                "page_code": normalized_page_code,
                "locale": normalized_locale,
                "draft_version": int(page["draft_version"]),
                "admin_id": normalized_admin_user_id,
                "iat": now,
                "exp": expires_at,
                "jti": uuid4().hex,
            }
            token = jwt.encode(payload, _preview_secret(), algorithm="HS256")
            _record_page_audit(
                cursor=cursor,
                admin_user_id=normalized_admin_user_id,
                action_kind="site_v3.preview_token.issue",
                page=page,
                payload_extra={
                    "draft_version": int(page["draft_version"]),
                    "expires_at": expires_at.isoformat(),
                    "jti": payload["jti"],
                },
            )

    return {
        "token": token,
        "preview_url": f"{settings.site_v3_public_base_url}/preview/{token}",
        "expires_at": expires_at.isoformat(),
        "draft_version": int(page["draft_version"]),
    }


def validate_draft_preview_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _preview_secret(), algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise AppError("SITEV3.PREVIEW.TOKEN_EXPIRED") from exc
    except InvalidTokenError as exc:
        raise AppError("SITEV3.PREVIEW.TOKEN_INVALID") from exc

    if payload.get("typ") != TOKEN_TYPE:
        raise AppError("SITEV3.PREVIEW.TOKEN_INVALID")
    required = ("site_code", "page_code", "locale", "draft_version", "admin_id")
    if any(key not in payload for key in required):
        raise AppError("SITEV3.PREVIEW.TOKEN_INVALID")
    return payload


def build_draft_snapshot(
    *,
    site_code: str,
    page_code: str,
    locale: str,
    token_payload: dict[str, Any],
) -> dict[str, object]:
    normalized_site_code = _normalize_code(site_code, "Site code is required", max_length=32)
    normalized_page_code = _normalize_code(page_code, "Page code is required", max_length=64)
    normalized_locale = _normalize_locale(locale)
    _assert_token_scope(
        token_payload=token_payload,
        site_code=normalized_site_code,
        page_code=normalized_page_code,
        locale=normalized_locale,
    )

    with db_connection() as connection:
        with connection.cursor() as cursor:
            _require_site(cursor=cursor, site_code=normalized_site_code)
            page = repository.load_page(
                cursor=cursor,
                site_code=normalized_site_code,
                page_code=normalized_page_code,
                locale=normalized_locale,
            )
            if page is None:
                raise AppError("SITEV3.PREVIEW.PAGE_NOT_FOUND")
            current_draft_version = int(page["draft_version"])
            token_draft_version = int(token_payload["draft_version"])
            if token_draft_version < current_draft_version:
                raise AppError(
                    "SITEV3.PREVIEW.TOKEN_STALE",
                    details={"draft_version": current_draft_version},
                )
            modules = repository.list_modules(cursor=cursor, page_id=str(page["id"]))

    return build_snapshot_from_modules(
        page=page,
        modules=modules,
        version_key="draft_version",
        version=current_draft_version,
        is_preview=True,
    )


def _assert_token_scope(
    *,
    token_payload: dict[str, Any],
    site_code: str,
    page_code: str,
    locale: str,
) -> None:
    if (
        token_payload.get("site_code") != site_code
        or token_payload.get("page_code") != page_code
        or token_payload.get("locale") != locale
    ):
        raise AppError("SITEV3.PREVIEW.TOKEN_SCOPE_MISMATCH")


def _preview_secret() -> str:
    secret = settings.site_v3_draft_preview_secret.strip()
    if not secret:
        raise AppError("CK.SYSTEM.SERVICE_UNAVAILABLE")
    return secret
