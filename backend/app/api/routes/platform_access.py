from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player
from app.api.responses import error_response
from app.modules.platform.access_sessions.service import (
    AccessSessionNotFoundError,
    AccessSessionStateConflictError,
    AccessSessionValidationError,
    create_access_session,
    ping_access_session,
)

router = APIRouter(prefix="/access-sessions", tags=["platform-access-sessions"])


class CreateAccessSessionRequest(BaseModel):
    game_code: str


@router.post("")
def create_platform_access_session(
    payload: CreateAccessSessionRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = create_access_session(
            user_id=str(current_user["id"]),
            game_code=payload.game_code,
        )
    except AccessSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/{access_session_id}/ping")
def ping_platform_access_session(
    access_session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = ping_access_session(
            user_id=str(current_user["id"]),
            access_session_id=access_session_id,
        )
    except AccessSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AccessSessionNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AccessSessionStateConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="GAME_STATE_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }
