from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aistruth_api.config import get_settings
from aistruth_api.routes import debug_geodnet, demo, health, nearest, norway_ais, validate

if TYPE_CHECKING:
    from asyncpg import Pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool: Pool | None = None
    if settings.database_url:
        pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    app.state.db_pool = pool
    yield
    if pool is not None:
        await pool.close()


def create_app() -> FastAPI:
    app = FastAPI(title="AISTruth API", version="0.1.0", lifespan=lifespan)
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(health.router)
    app.include_router(demo.router, prefix="/v1")
    app.include_router(nearest.router, prefix="/v1")
    app.include_router(norway_ais.router, prefix="/v1")
    app.include_router(validate.router, prefix="/v1")
    if settings.enable_geodnet_debug_routes:
        app.include_router(debug_geodnet.router, prefix="/v1")
    return app


app = create_app()
