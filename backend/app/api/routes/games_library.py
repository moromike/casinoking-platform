from fastapi import APIRouter, Query, status

from app.api.responses import error_response
from app.modules.platform.catalog.library_service import get_site_game_library
from app.modules.platform.catalog.service import CatalogNotFoundError, CatalogValidationError

router = APIRouter(prefix="/games/library", tags=["games-library"])


@router.get("")
def get_games_library(site_code: str = Query(default="casinoking")) -> dict[str, object] | object:
    try:
        library = get_site_game_library(site_code=site_code)
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

    return {"success": True, "data": library}
