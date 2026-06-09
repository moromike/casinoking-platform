from fastapi.responses import JSONResponse

from app.api.errors import build_error_response


def envelope(data: object) -> dict[str, object]:
    return {
        "success": True,
        "data": data,
    }


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return build_error_response(
        status_code=status_code,
        code=code,
        message=message,
        details=details,
    )
