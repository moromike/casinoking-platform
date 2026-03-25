from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.responses import error_response
from app.core.config import settings

router = APIRouter(prefix="/site", tags=["site"])


class SiteAccessRequest(BaseModel):
    password: str


@router.post("/access")
def site_access(payload: SiteAccessRequest) -> dict[str, object]:
    if payload.password != settings.site_access_password:
        return error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid site access password",
        )

    return {
        "success": True,
        "data": {
            "access_granted": True,
        },
    }
