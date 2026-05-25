from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.responses import envelope
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
