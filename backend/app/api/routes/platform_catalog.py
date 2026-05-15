from fastapi import APIRouter, Query, status

from app.api.responses import error_response
from app.modules.platform.catalog.service import (
    CatalogNotFoundError,
    CatalogValidationError,
    get_title_catalog_entry,
    list_site_titles,
)

router = APIRouter(prefix="/catalog", tags=["platform-catalog"])


@router.get("/titles/{title_code}")
def get_catalog_title(title_code: str) -> dict[str, object] | object:
    try:
        result = get_title_catalog_entry(title_code=title_code)
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

    return {"success": True, "data": result}


@router.get("/sites/{site_code}/titles")
def get_catalog_site_titles(
    site_code: str,
    status_filter: str = Query(default="all", alias="status"),
    test_filter: str = Query(default="all", alias="test"),
) -> dict[str, object] | object:
    try:
        result = list_site_titles(
            site_code=site_code,
            status_filter=status_filter,
            test_filter=test_filter,
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

    return {"success": True, "data": result}
