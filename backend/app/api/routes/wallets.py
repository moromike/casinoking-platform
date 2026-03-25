from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.api.responses import error_response
from app.modules.wallet.service import (
    get_wallet_for_user,
    list_wallets_for_user,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("")
def list_wallets(
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    return {
        "success": True,
        "data": list_wallets_for_user(str(current_user["id"])),
    }


@router.get("/{wallet_type}")
def get_wallet(
    wallet_type: str,
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    result = get_wallet_for_user(
        user_id=str(current_user["id"]),
        wallet_type=wallet_type,
    )
    if result is None:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message="Wallet not found",
        )

    return {
        "success": True,
        "data": result,
    }
