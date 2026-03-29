from fastapi import APIRouter, Depends, Header, Query, status
from pydantic import BaseModel

from app.api.dependencies import get_current_admin
from app.api.responses import error_response
from app.modules.games.mines.backoffice_config import (
    MinesBackofficeValidationError,
    get_admin_backoffice_config,
    publish_admin_backoffice_config,
    update_admin_backoffice_draft,
)
from app.modules.admin.service import (
    AdminIdempotencyConflictError,
    AdminInsufficientBalanceError,
    AdminNotFoundError,
    AdminValidationError,
    create_bonus_grant,
    create_wallet_adjustment,
    get_ledger_report_for_admin,
    list_users_for_admin,
    suspend_user_for_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminAdjustmentRequest(BaseModel):
    wallet_type: str
    direction: str
    amount: str
    reason: str


class BonusGrantRequest(BaseModel):
    amount: str
    reason: str


class ModeUiLabelsRequest(BaseModel):
    bet: str
    bet_loading: str
    collect: str
    collect_loading: str
    home: str
    fullscreen: str
    game_info: str


class BoardAssetsRequest(BaseModel):
    safe_icon_data_url: str | None = None
    mine_icon_data_url: str | None = None


class MinesBackofficeConfigRequest(BaseModel):
    rules_sections: dict[str, str]
    published_grid_sizes: list[int]
    published_mine_counts: dict[str, list[int]]
    default_mine_counts: dict[str, int]
    ui_labels: dict[str, ModeUiLabelsRequest]
    board_assets: BoardAssetsRequest


@router.get("/users")
def list_users(
    email: str | None = Query(default=None),
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": list_users_for_admin(email_query=email),
    }


@router.get("/reports/ledger")
def get_ledger_report(
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": get_ledger_report_for_admin(),
    }


@router.post("/users/{target_user_id}/suspend")
def suspend_user(
    target_user_id: str,
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = suspend_user_for_admin(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.get("/games/mines/backoffice-config")
def get_mines_backoffice_config(
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    return {
        "success": True,
        "data": get_admin_backoffice_config(),
    }


@router.put("/games/mines/backoffice-config")
def put_mines_backoffice_config(
    payload: MinesBackofficeConfigRequest,
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = update_admin_backoffice_draft(
            admin_user_id=str(current_admin["id"]),
            rules_sections=payload.rules_sections,
            published_grid_sizes=payload.published_grid_sizes,
            published_mine_counts=payload.published_mine_counts,
            default_mine_counts=payload.default_mine_counts,
            ui_labels={
                mode: labels.model_dump()
                for mode, labels in payload.ui_labels.items()
            },
            board_assets=payload.board_assets.model_dump(),
        )
    except MinesBackofficeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/games/mines/backoffice-config/publish")
def publish_mines_backoffice_config(
    current_admin: dict[str, object] | object = Depends(get_current_admin),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin

    try:
        result = publish_admin_backoffice_config(
            admin_user_id=str(current_admin["id"]),
        )
    except MinesBackofficeValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/users/{target_user_id}/adjustments")
def create_adjustment(
    target_user_id: str,
    payload: AdminAdjustmentRequest,
    current_admin: dict[str, object] | object = Depends(get_current_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )

    try:
        result = create_wallet_adjustment(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
            idempotency_key=idempotency_key,
            wallet_type=payload.wallet_type,
            direction=payload.direction,
            amount=payload.amount,
            reason=payload.reason,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AdminInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except AdminIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/users/{target_user_id}/bonus-grants")
def create_bonus(
    target_user_id: str,
    payload: BonusGrantRequest,
    current_admin: dict[str, object] | object = Depends(get_current_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, object] | object:
    if not isinstance(current_admin, dict):
        return current_admin
    if not idempotency_key:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Idempotency-Key header is required",
        )

    try:
        result = create_bonus_grant(
            admin_user_id=str(current_admin["id"]),
            target_user_id=target_user_id,
            idempotency_key=idempotency_key,
            amount=payload.amount,
            reason=payload.reason,
        )
    except AdminValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AdminNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )
    except AdminInsufficientBalanceError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="INSUFFICIENT_BALANCE",
            message=str(exc),
        )
    except AdminIdempotencyConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }
