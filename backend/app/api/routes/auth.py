from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import get_current_player, get_current_user
from app.api.responses import error_response
from app.modules.auth.service import (
    AuthConflictError,
    AuthForbiddenError,
    AuthInvalidCredentialsError,
    AuthPreconditionError,
    AuthResetTokenError,
    AuthValidationError,
    authenticate_user,
    change_password,
    provision_demo_player,
    request_password_reset,
    register_player,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    site_access_password: str
    first_name: str | None = None
    last_name: str | None = None
    fiscal_code: str | None = None
    phone_number: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.get("/me")
def get_me(
    current_user: dict[str, object] | object = Depends(get_current_user),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    return {
        "success": True,
        "data": current_user,
    }


@router.post("/demo")
def demo_login() -> dict[str, object] | object:
    try:
        result = provision_demo_player()
    except AuthConflictError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
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


@router.post("/register")
def register(payload: RegisterRequest) -> dict[str, object] | object:
    try:
        result = register_player(
            email=payload.email,
            password=payload.password,
            site_access_password=payload.site_access_password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            fiscal_code=payload.fiscal_code,
            phone_number=payload.phone_number,
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


@router.post("/password/forgot")
def forgot_password(payload: ForgotPasswordRequest) -> dict[str, object] | object:
    try:
        result = request_password_reset(email=payload.email)
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )

    return {
        "success": True,
        "data": result,
    }


@router.post("/password/reset")
def complete_password_reset(payload: ResetPasswordRequest) -> dict[str, object] | object:
    try:
        result = reset_password(
            token=payload.token,
            new_password=payload.new_password,
        )
    except AuthValidationError as exc:
        return error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(exc),
        )
    except AuthResetTokenError as exc:
        return error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="VALIDATION_ERROR",
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


@router.post("/password/change")
def change_current_password(
    payload: ChangePasswordRequest,
    current_user: dict[str, object] | object = Depends(get_current_player),
) -> dict[str, object] | object:
    if not isinstance(current_user, dict):
        return current_user

    try:
        result = change_password(
            user_id=str(current_user["id"]),
            old_password=payload.old_password,
            new_password=payload.new_password,
            required_role="player",
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


@router.post("/login")
def login(payload: LoginRequest) -> dict[str, object] | object:
    try:
        result = authenticate_user(
            email=payload.email,
            password=payload.password,
            required_role="player",
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
