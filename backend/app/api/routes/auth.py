from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.responses import error_response
from app.modules.auth.service import (
    AuthConflictError,
    AuthForbiddenError,
    AuthInvalidCredentialsError,
    AuthPreconditionError,
    AuthValidationError,
    authenticate_user,
    register_player,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    site_access_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(payload: RegisterRequest) -> dict[str, object] | object:
    try:
        result = register_player(
            email=payload.email,
            password=payload.password,
            site_access_password=payload.site_access_password,
        )
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthConflictError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
            details={"field": "email"},
        )
    except AuthPreconditionError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, object] | object:
    try:
        result = authenticate_user(
            email=payload.email,
            password=payload.password,
        )
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthInvalidCredentialsError as exc:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=str(exc),
        )
    except AuthForbiddenError as exc:
        return error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }
