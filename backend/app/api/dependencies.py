from fastapi import Header, status
import jwt

from app.api.responses import error_response
from app.core.config import settings
from app.modules.auth.service import get_user_by_id


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
    if not isinstance(user_id, str) or not user_id:
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

    return current_user
