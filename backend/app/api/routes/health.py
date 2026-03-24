from fastapi import APIRouter

router = APIRouter(prefix="/health")


@router.get("/live")
def live() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "status": "live",
            "service": "backend",
        },
    }


@router.get("/ready")
def ready() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "status": "ready",
            "service": "backend",
            "checks": {
                "app": "ok",
            },
        },
    }
