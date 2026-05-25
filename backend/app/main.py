from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.modules.platform.access_sessions.service import timeout_expired_access_sessions


logger = logging.getLogger(__name__)
ACCESS_SESSION_SWEEP_INTERVAL_SECONDS = 30


@asynccontextmanager
async def lifespan(app: FastAPI):
    sweep_task = asyncio.create_task(_access_session_timeout_loop())
    try:
        yield
    finally:
        sweep_task.cancel()
        with suppress(asyncio.CancelledError):
            await sweep_task


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    settings.asset_storage_root.mkdir(parents=True, exist_ok=True)
    site_asset_storage_root = settings.asset_storage_root / "sites"
    site_asset_storage_root.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/static/games",
        StaticFiles(directory=settings.asset_storage_root),
        name="game_assets",
    )
    app.mount(
        "/static/sites",
        StaticFiles(directory=site_asset_storage_root),
        name="site_assets",
    )
    return app


async def _access_session_timeout_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(timeout_expired_access_sessions)
        except Exception:
            logger.exception("Access-session timeout sweep failed")
        await asyncio.sleep(ACCESS_SESSION_SWEEP_INTERVAL_SECONDS)


app = create_app()
