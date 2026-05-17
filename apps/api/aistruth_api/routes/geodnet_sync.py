"""GEODNET RTK station catalog sync into PostGIS."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations.geodnet_station_sync import sync_geodnet_stations_from_settings
from aistruth_api.rate_limit import limiter
from aistruth_api.schemas import GeodnetSyncResponse

router = APIRouter(tags=["geodnet"])
log = logging.getLogger(__name__)


@router.post("/geodnet/sync-stations", response_model=GeodnetSyncResponse)
@limiter.limit("12/minute")
async def sync_geodnet_stations(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> GeodnetSyncResponse:
    """Pull RTK ``/api/v3/station/list`` using enterprise credentials; upsert ``geodnet_nodes``.

    Demo/fixture rows (``ingest_source='fixture'``) are not removed. Live stations use ids
    ``geodnet:<station name>``.
    """
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "DATABASE_URL not set or pool unavailable. "
                "Run migrations and start Postgres before syncing stations."
            ),
        )
    if not settings.geodnet_rtk_app_id or not settings.geodnet_rtk_app_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "GEODNET RTK API is not configured. Set GEODNET_RTK_APP_ID and "
                "GEODNET_RTK_APP_KEY (enterprise credentials from GEODNET)."
            ),
        )
    try:
        upserted = await sync_geodnet_stations_from_settings(pool, settings)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GEODNET RTK API response error: {exc}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GEODNET RTK HTTP {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="GEODNET RTK HTTP request failed",
        ) from exc

    log.info("geodnet sync-stations upserted=%s", upserted)
    return GeodnetSyncResponse(upserted=upserted)
