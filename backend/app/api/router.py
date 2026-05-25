from fastapi import APIRouter

from app.api.routes.account import router as account_router
from app.api.routes.admin_assets import router as admin_assets_router
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.boxe import router as boxe_router
from app.api.routes.cms_v2 import router as cms_v2_router
from app.api.routes.demo import router as demo_router
from app.api.routes.health import router as health_router
from app.api.routes.hi_lo import router as hi_lo_router
from app.api.routes.games_library import router as games_library_router
from app.api.routes.ledger import router as ledger_router
from app.api.routes.mines import router as mines_router
from app.api.routes.platform_access import router as platform_access_router
from app.api.routes.platform_catalog import router as platform_catalog_router
from app.api.routes.platform_settings import router as platform_settings_router
from app.api.routes.platform_table_sessions import router as platform_table_sessions_router
from app.api.routes.site_access import router as site_access_router
from app.api.routes.site_cms import router as site_cms_router
from app.api.routes.site_v3_admin import router as site_v3_admin_router
from app.api.routes.site_v3_public import router as site_v3_public_router
from app.api.routes.title_theme import admin_router as admin_title_theme_router
from app.api.routes.title_theme import router as title_theme_router
from app.api.routes.wallets import router as wallets_router

api_router = APIRouter()
api_router.include_router(account_router)
api_router.include_router(admin_assets_router)
api_router.include_router(admin_title_theme_router)
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(boxe_router)
api_router.include_router(cms_v2_router)
api_router.include_router(demo_router)
api_router.include_router(games_library_router)
api_router.include_router(health_router, tags=["health"])
api_router.include_router(hi_lo_router)
api_router.include_router(ledger_router)
api_router.include_router(mines_router)
api_router.include_router(platform_access_router)
api_router.include_router(platform_catalog_router)
api_router.include_router(platform_settings_router)
api_router.include_router(platform_table_sessions_router)
api_router.include_router(site_access_router)
api_router.include_router(site_cms_router)
api_router.include_router(site_v3_admin_router)
api_router.include_router(site_v3_public_router)
api_router.include_router(title_theme_router)
api_router.include_router(wallets_router)
