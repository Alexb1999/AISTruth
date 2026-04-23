from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import asyncpg
from fastapi import FastAPI

from aistruth_api.config import get_settings
from aistruth_api.routes import demo, health, nearest, norway_ais, validate

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
    app.include_router(health.router)
    app.include_router(demo.router, prefix="/v1")
    app.include_router(nearest.router, prefix="/v1")
    app.include_router(norway_ais.router, prefix="/v1")
    app.include_router(validate.router, prefix="/v1")
    return app


app = create_app()
