from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.responses import error_response
from app.modules.auth.service import (
    AuthConflictError,
    AuthForbiddenError,
    AuthInvalidCredentialsError,
    AuthPreconditionError,
    AuthResetTokenError,
    AuthValidationError,
    authenticate_user,
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


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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
