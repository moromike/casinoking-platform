from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.api.dependencies import require_admin_area
from app.api.responses import error_response
from app.modules.platform.site_cms.service import (
    SiteCmsConflictError,
    SiteCmsNotFoundError,
    SiteCmsValidationError,
    create_home_slot,
    list_admin_home_slots,
    list_public_home_slots,
    update_home_slot,
)


router = APIRouter(tags=["site-cms"])


class SiteHomeSlotCreateRequest(BaseModel):
    slot_key: str
    title: str
    subtitle: str | None = None
    cta_label: str | None = None
    cta_target_type: str = "none"
    cta_target_ref: str | None = None
    media_asset_id: str | None = None
    sort_order: int = 0
    status: str = "draft"
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class SiteHomeSlotUpdateRequest(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    cta_label: str | None = None
    cta_target_type: str | None = None
    cta_target_ref: str | None = None
    media_asset_id: str | None = None
    sort_order: int | None = None
    status: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


@router.get("/site/home")
def get_public_site_home(site_code: str = Query(default="casinoking")) -> dict[str, object] | object:
    try:
        result = list_public_home_slots(site_code=site_code)
    except SiteCmsValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except SiteCmsNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": result}


@router.get("/admin/sites/{site_code}/home-slots")
def get_admin_site_home_slots(
    site_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = list_admin_home_slots(site_code=site_code)
    except SiteCmsValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except SiteCmsNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": result}


@router.post("/admin/sites/{site_code}/home-slots")
def post_admin_site_home_slot(
    site_code: str,
    payload: SiteHomeSlotCreateRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = create_home_slot(
            admin_user_id=str(current_admin["id"]),
            site_code=site_code,
            slot_key=payload.slot_key,
            title=payload.title,
            subtitle=payload.subtitle,
            cta_label=payload.cta_label,
            cta_target_type=payload.cta_target_type,
            cta_target_ref=payload.cta_target_ref,
            media_asset_id=payload.media_asset_id,
            sort_order=payload.sort_order,
            status=payload.status,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
    except SiteCmsConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=str(exc),
        )
    except SiteCmsValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except SiteCmsNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": result}


@router.patch("/admin/sites/{site_code}/home-slots/{slot_key}")
def patch_admin_site_home_slot(
    site_code: str,
    slot_key: str,
    payload: SiteHomeSlotUpdateRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = update_home_slot(
            admin_user_id=str(current_admin["id"]),
            site_code=site_code,
            slot_key=slot_key,
            updates=payload.model_dump(exclude_unset=True),
        )
    except SiteCmsValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except SiteCmsNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": result}
