from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_player
from app.api.responses import error_response
from app.modules.account.service import (
    AccountCursorError,
    AccountStatementNotFoundError,
    AccountStatementValidationError,
    DEFAULT_STATEMENT_CATEGORY,
    DEFAULT_STATEMENT_DETAIL_LIMIT,
    DEFAULT_STATEMENT_MOVEMENT_LIMIT,
    DEFAULT_STATEMENT_PERIOD,
    DEFAULT_STATEMENT_WALLET_TYPE,
    DEFAULT_WALLET_MOVEMENT_LIMIT,
    MAX_STATEMENT_DETAIL_LIMIT,
    MAX_STATEMENT_MOVEMENT_LIMIT,
    MAX_WALLET_MOVEMENT_LIMIT,
    get_statement_movement_detail_for_user,
    list_statement_movements_for_user,
    list_wallet_movements_for_user,
)

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/statement-movements")
def list_statement_movements(
    category: str = Query(default=DEFAULT_STATEMENT_CATEGORY),
    wallet_type: str = Query(default=DEFAULT_STATEMENT_WALLET_TYPE),
    period: str = Query(default=DEFAULT_STATEMENT_PERIOD),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(
        default=DEFAULT_STATEMENT_MOVEMENT_LIMIT,
        ge=1,
        le=MAX_STATEMENT_MOVEMENT_LIMIT,
    ),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        page = list_statement_movements_for_user(
            user_id=str(current_user["id"]),
            category=category,
            wallet_type=wallet_type,
            period=period,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )
    except (AccountCursorError, AccountStatementValidationError) as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": page["items"],
        "meta": {
            "next_cursor": page["next_cursor"],
            "limit": page["limit"],
            "category": page["category"],
            "wallet_type": page["wallet_type"],
            "period": page["period"],
            "date_from": page["date_from"],
            "date_to": page["date_to"],
            "balance_disclaimer": page["balance_disclaimer"],
        },
    }


@router.get("/statement-movements/{movement_id:path}")
def get_statement_movement_detail(
    movement_id: str,
    wallet_type: str = Query(default=DEFAULT_STATEMENT_WALLET_TYPE),
    limit: int = Query(
        default=DEFAULT_STATEMENT_DETAIL_LIMIT,
        ge=1,
        le=MAX_STATEMENT_DETAIL_LIMIT,
    ),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        detail = get_statement_movement_detail_for_user(
            user_id=str(current_user["id"]),
            movement_id=movement_id,
            wallet_type=wallet_type,
            limit=limit,
            cursor=cursor,
        )
    except (AccountCursorError, AccountStatementValidationError) as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AccountStatementNotFoundError as exc:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=str(exc),
        )

    return {
        "success": True,
        "data": {
            "movement_id": detail["movement_id"],
            "movement_family": detail["movement_family"],
            "items": detail["items"],
        },
        "meta": {
            "next_cursor": detail["next_cursor"],
            "limit": detail["limit"],
            "wallet_type": detail["wallet_type"],
        },
    }


@router.get("/wallet-movements")
def list_wallet_movements(
    limit: int = Query(
        default=DEFAULT_WALLET_MOVEMENT_LIMIT,
        ge=1,
        le=MAX_WALLET_MOVEMENT_LIMIT,
    ),
    cursor: str | None = Query(default=None),
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        page = list_wallet_movements_for_user(
            user_id=str(current_user["id"]),
            limit=limit,
            cursor=cursor,
        )
    except AccountCursorError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": page["items"],
        "meta": {
            "next_cursor": page["next_cursor"],
            "limit": page["limit"],
        },
    }
