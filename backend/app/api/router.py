from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.ledger import router as ledger_router
from app.api.routes.mines import router as mines_router
from app.api.routes.platform_access import router as platform_access_router
from app.api.routes.site_access import router as site_access_router
from app.api.routes.wallets import router as wallets_router

api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(health_router, tags=["health"])
api_router.include_router(ledger_router)
api_router.include_router(mines_router)
api_router.include_router(platform_access_router)
api_router.include_router(site_access_router)
api_router.include_router(wallets_router)
