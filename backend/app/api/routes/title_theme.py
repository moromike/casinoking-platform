from pydantic import BaseModel
from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import require_admin_area
from app.api.responses import error_response
from app.modules.platform.catalog.theme_service import (
    ThemeNotFoundError,
    ThemeValidationError,
    get_admin_title_theme,
    publish_admin_title_theme,
    resolve_title_theme,
    update_admin_title_theme_draft,
)

router = APIRouter(prefix="/titles/{title_code}/theme", tags=["title-theme"])
admin_router = APIRouter(prefix="/admin/titles/{title_code}/theme", tags=["admin-title-theme"])


class AdminTitleThemeRequest(BaseModel):
    tokens: dict[str, object]


@router.get("")
def get_title_theme(title_code: str, response: Response) -> dict[str, object] | object:
    try:
        theme = resolve_title_theme(title_code=title_code)
    except ThemeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ThemeNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    response.headers["ETag"] = str(theme["etag"])
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"success": True, "data": theme}


@admin_router.get("")
def get_admin_theme(
    title_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        theme = get_admin_title_theme(title_code=title_code)
    except ThemeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ThemeNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": theme}


@admin_router.put("")
def put_admin_theme(
    title_code: str,
    payload: AdminTitleThemeRequest,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        theme = update_admin_title_theme_draft(
            title_code=title_code,
            tokens=payload.tokens,
            admin_user_id=str(current_admin["id"]),
        )
    except ThemeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ThemeNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": theme}


@admin_router.post("/publish")
def post_admin_theme_publish(
    title_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        theme = publish_admin_title_theme(
            title_code=title_code,
            admin_user_id=str(current_admin["id"]),
        )
    except ThemeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except ThemeNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": theme}
