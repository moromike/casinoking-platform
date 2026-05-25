from fastapi import Depends, Header, HTTPException, status
import jwt

from app.api.responses import error_response
from app.core.config import settings
from app.modules.auth.service import get_user_by_id
from app.modules.admin.service import get_admin_profile


def get_bearer_token(
    authorization: str | None = Header(default=None),
) -> str | object:
    if authorization is None or not authorization.startswith("Bearer "):
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Missing or invalid bearer token",
        )
    return authorization.removeprefix("Bearer ").strip()


def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, object] | object:
    token = get_bearer_token(authorization)
    if not isinstance(token, str):
        return token

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
    except jwt.InvalidTokenError:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid bearer token",
        )

    user_id = payload.get("sub")
    token_kind = payload.get("token_kind")
    if not isinstance(user_id, str) or not user_id:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid bearer token",
        )
    if token_kind not in (None, "access"):
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid bearer token",
        )

    user = get_user_by_id(user_id)
    if user is None:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authenticated user not found",
        )

    if user["status"] != "active":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Account is not active",
        )

    return user


def get_current_admin(
    authorization: str | None = Header(default=None),
) -> dict[str, object] | object:
    current_user = get_current_user(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if current_user["role"] != "admin":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Role is not valid for this endpoint",
        )

    # Enrich with admin_profiles data (is_superadmin, areas). A missing profile
    # is no longer treated as superadmin: admin authorization must be explicit.
    user_id = str(current_user["id"])
    profile = get_admin_profile(user_id=user_id)
    if profile is not None:
        current_user = {
            **current_user,
            "is_superadmin": profile["is_superadmin"],
            "areas": profile["areas"],
        }
    else:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CK.AUTH.FORBIDDEN",
            message="Admin profile is required for this endpoint",
        )

    return current_user


def get_current_player(
    authorization: str | None = Header(default=None),
) -> dict[str, object] | object:
    current_user = get_current_user(authorization)
    if not isinstance(current_user, dict):
        return current_user

    if current_user["role"] != "player":
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Role is not valid for this endpoint",
        )

    return current_user


def require_admin_area(area: str):
    """
    Dependency factory that checks whether the current admin has access to a given area.

    An admin passes if:
      - is_superadmin is True, OR
      - area is in their areas list

    Raises HTTP 403 if the check fails.

    Usage in route:
        @router.get("/some/route")
        def my_route(
            current_admin: dict | object = Depends(require_admin_area("finance")),
        ):
            if not isinstance(current_admin, dict):
                return current_admin
            ...
    """
    requested_area = _canonical_admin_area(area)

    def _check_area(
        current_admin: dict[str, object] | object = Depends(get_current_admin),
    ) -> dict[str, object] | object:
        # Propagate auth errors (401/403 from get_current_admin)
        if not isinstance(current_admin, dict):
            return current_admin

        is_superadmin = current_admin.get("is_superadmin", False)
        areas = {
            _canonical_admin_area(str(area_name))
            for area_name in current_admin.get("areas", [])
        }

        # "superadmin" is a virtual area — only superadmins pass
        if requested_area == "superadmin":
            if not is_superadmin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "Only superadmin can access this endpoint",
                        },
                    },
                )
            return current_admin

        if is_superadmin or requested_area in areas:
            return current_admin

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": f"Access to area '{requested_area}' is not permitted for this admin account",
                },
            },
        )

    return _check_area


def _canonical_admin_area(area: str) -> str:
    normalized = area.strip().lower()
    return "games" if normalized == "mines" else normalized
