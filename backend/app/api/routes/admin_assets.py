from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies import require_admin_area
from app.api.responses import error_response
from app.modules.platform.asset_registry.service import (
    AssetRegistryNotFoundError,
    AssetRegistryValidationError,
    AssetUpload,
    delete_title_asset,
    list_title_assets,
    upload_title_asset,
)
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    ensure_title_is_mutable,
)

router = APIRouter(prefix="/admin/titles/{title_code}/assets", tags=["admin-assets"])


@router.get("")
def get_title_assets(
    title_code: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        assets = list_title_assets(title_code=title_code)
    except AssetRegistryValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AssetRegistryNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": assets}


@router.post("")
async def post_title_asset(
    title_code: str,
    asset_kind: str = Form(...),
    file: UploadFile = File(...),
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    content = await file.read()
    try:
        ensure_title_is_mutable(title_code=title_code)
        asset = upload_title_asset(
            AssetUpload(
                title_code=title_code,
                asset_kind=asset_kind,
                mime=file.content_type or "",
                content=content,
                uploaded_by_admin_user_id=str(current_admin["id"]),
            )
        )
    except CatalogValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except CatalogNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AssetRegistryValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AssetRegistryNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": asset}


@router.delete("/{asset_kind}")
def delete_title_asset_endpoint(
    title_code: str,
    asset_kind: str,
    current_admin: dict[str, object] | object = Depends(require_admin_area("mines")),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        ensure_title_is_mutable(title_code=title_code)
        asset = delete_title_asset(
            title_code=title_code,
            asset_kind=asset_kind,
            admin_user_id=str(current_admin["id"]),
        )
    except CatalogValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except CatalogNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AssetRegistryValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AssetRegistryNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": asset}
