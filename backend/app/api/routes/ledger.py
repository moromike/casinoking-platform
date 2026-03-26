from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.api.responses import error_response
from app.modules.ledger.service import (
    get_transaction_detail_for_viewer,
    list_transactions_for_viewer,
    transaction_exists,
)

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/transactions")
def list_transactions(
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    return {
        "success": True,
        "data": list_transactions_for_viewer(
            viewer_user_id=str(current_user["id"]),
            viewer_role=str(current_user["role"]),
        ),
    }


@router.get("/transactions/{transaction_id}")
def get_transaction_detail(
    transaction_id: str,
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    result = get_transaction_detail_for_viewer(
        viewer_user_id=str(current_user["id"]),
        viewer_role=str(current_user["role"]),
        transaction_id=transaction_id,
    )
    if result is None:
        from fastapi import status

        if transaction_exists(transaction_id):
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Transaction ownership is not valid",
            )

        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Transaction not found",
        )

    return {
        "success": True,
        "data": result,
    }
