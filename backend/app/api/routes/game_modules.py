from fastapi import APIRouter, status

from app.api.responses import error_response
from app.modules.platform.game_modules.manifest import (
    GameModuleManifestNotFoundError,
    get_game_module_manifest,
    serialize_game_module_manifest,
)

router = APIRouter(prefix="/game-modules", tags=["game-modules"])


@router.get("/{game_code}/manifest")
def get_game_module_manifest_route(game_code: str) -> dict[str, object] | object:
    try:
        manifest = get_game_module_manifest(game_code)
    except GameModuleManifestNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {"success": True, "data": serialize_game_module_manifest(manifest)}
