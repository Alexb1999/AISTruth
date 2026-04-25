from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, cast

import asyncpg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.types import ExceptionHandler

from aistruth_api.config import get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.logging import configure_logging, request_id_middleware
from aistruth_api.rate_limit import limiter
from aistruth_api.routes import debug_geodnet, demo, health, nearest, norway_ais, validate
from aistruth_api.security import require_api_key

if TYPE_CHECKING:
    from asyncpg import Pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    pool: Pool | None = None
    if settings.database_url:
        pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    app.state.db_pool = pool
    yield
    if pool is not None:
        await pool.close()
    await barentswatch_client.close_default_client()


def create_app() -> FastAPI:
    configure_logging()
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
    app.middleware("http")(request_id_middleware)
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,
        cast(ExceptionHandler, _rate_limit_exceeded_handler),
    )
    app.add_middleware(SlowAPIMiddleware)
    protected = [Depends(require_api_key)]
    app.include_router(health.router)
    app.include_router(demo.router, prefix="/v1", dependencies=protected)
    app.include_router(nearest.router, prefix="/v1", dependencies=protected)
    app.include_router(norway_ais.router, prefix="/v1", dependencies=protected)
    app.include_router(validate.router, prefix="/v1", dependencies=protected)
    if settings.enable_geodnet_debug_routes:
        app.include_router(debug_geodnet.router, prefix="/v1", dependencies=protected)
    return app


app = create_app()
