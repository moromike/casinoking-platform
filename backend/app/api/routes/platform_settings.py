from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.api.responses import envelope, error_response
from app.modules.admin.service import get_admin_profile
from app.modules.platform.settings.service import build_platform_settings_inventory


router = APIRouter(prefix="/admin/platform-settings", tags=["admin-platform-settings"])


@router.get("")
def get_platform_settings_inventory(
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    if current_user.get("role") != "admin":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CK.AUTH.FORBIDDEN",
            message="Only explicit superadmin profiles can access Platform Settings.",
        )

    profile = get_admin_profile(user_id=str(current_user["id"]))
    if profile is None or profile.get("is_superadmin") is not True:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CK.AUTH.FORBIDDEN",
            message="Only explicit superadmin profiles can access Platform Settings.",
        )

    return envelope(build_platform_settings_inventory())
