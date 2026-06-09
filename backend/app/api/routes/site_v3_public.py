from __future__ import annotations

from fastapi import APIRouter, Header, Query, Response

from app.api.errors import AppError
from app.api.responses import envelope
from app.modules.platform.site_v3.preview_service import (
    build_draft_snapshot,
    validate_draft_preview_token,
)
from app.modules.platform.site_v3.service import (
    public_get_manifest,
    public_get_navigation,
    public_get_published_page,
)


router = APIRouter(prefix="/site-v3", tags=["site-v3-public"])


@router.get("/sites/{site_code}/pages/{page_code}")
def get_site_v3_public_page(
    site_code: str,
    page_code: str,
    locale: str = Query(default="it"),
) -> dict[str, object]:
    return envelope(
        public_get_published_page(
            site_code=site_code,
            page_code=page_code,
            locale=locale,
        )
    )


@router.get("/sites/{site_code}/pages/{page_code}/preview-draft")
def get_site_v3_public_preview_draft(
    site_code: str,
    page_code: str,
    response: Response,
    locale: str = Query(default="it"),
    draft_preview_token: str | None = Header(default=None, alias="X-Draft-Preview-Token"),
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    if not draft_preview_token:
        raise AppError("SITEV3.PREVIEW.TOKEN_MISSING")
    token_payload = validate_draft_preview_token(draft_preview_token)
    return envelope(
        build_draft_snapshot(
            site_code=site_code,
            page_code=page_code,
            locale=locale,
            token_payload=token_payload,
        )
    )


@router.get("/sites/{site_code}/navigation")
def get_site_v3_public_navigation(
    site_code: str,
    locale: str = Query(default="it"),
) -> dict[str, object]:
    return envelope(public_get_navigation(site_code=site_code, locale=locale))


@router.get("/sites/{site_code}/manifest")
def get_site_v3_public_manifest(
    site_code: str,
    locale: str = Query(default="it"),
) -> dict[str, object]:
    return envelope(public_get_manifest(site_code=site_code, locale=locale))
