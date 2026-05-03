from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player
from app.api.responses import error_response
from app.modules.platform.table_sessions.service import (
    TableSessionLimitExceededError,
    TableSessionNotFoundError,
    TableSessionStateConflictError,
    TableSessionValidationError,
    close_table_session,
    create_table_session,
    get_table_session,
    get_table_session_limits,
)

router = APIRouter(prefix="/table-sessions", tags=["platform-table-sessions"])


class CreateTableSessionRequest(BaseModel):
    game_code: str
    wallet_type: str = "cash"
    table_budget_amount: str
    access_session_id: str | None = None


@router.get("/limits")
def get_platform_table_session_limits(
    wallet_type: str = "cash",
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = get_table_session_limits(
            user_id=str(current_user["id"]),
            wallet_type=wallet_type,
        )
    except TableSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("")
def create_platform_table_session(
    payload: CreateTableSessionRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = create_table_session(
            user_id=str(current_user["id"]),
            game_code=payload.game_code,
            wallet_type=payload.wallet_type,
            table_budget_amount=payload.table_budget_amount,
            access_session_id=payload.access_session_id,
        )
    except TableSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except TableSessionLimitExceededError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="TABLE_LIMIT_EXCEEDED",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/{table_session_id}")
def get_platform_table_session(
    table_session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = get_table_session(
            user_id=str(current_user["id"]),
            table_session_id=table_session_id,
        )
    except TableSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except TableSessionNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/{table_session_id}/close")
def close_platform_table_session(
    table_session_id: str,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = close_table_session(
            user_id=str(current_user["id"]),
            table_session_id=table_session_id,
        )
    except TableSessionValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except TableSessionNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except TableSessionStateConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="GAME_STATE_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }
