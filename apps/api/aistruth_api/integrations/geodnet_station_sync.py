"""Fetch GEODNET RTK station list and upsert into PostGIS ``geodnet_nodes``."""

from __future__ import annotations

import logging
import time

import asyncpg
import httpx

from aistruth_api.config import Settings
from aistruth_core.geodnet_rtk import (
    GeodnetStation,
    parse_station_list_response,
    station_list_request_body,
)

log = logging.getLogger(__name__)


async def fetch_geodnet_station_list(
    *,
    api_base: str,
    app_id: str,
    app_key: str,
    region: str | None,
    timeout_s: float = 90.0,
    http_client: httpx.AsyncClient | None = None,
) -> list[GeodnetStation]:
    """Call ``POST {api_base}/api/v3/station/list`` with signed body."""
    body = station_list_request_body(
        app_id=app_id,
        app_key=app_key,
        time_ms=int(time.time() * 1000),
        region=region,
    )
    url = f"{api_base.rstrip('/')}/api/v3/station/list"

    async def _request(client: httpx.AsyncClient) -> list[GeodnetStation]:
        response = await client.post(url, json=body)
        response.raise_for_status()
        return parse_station_list_response(response.json())

    if http_client is not None:
        return await _request(http_client)

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        return await _request(client)


async def upsert_geodnet_stations(pool: asyncpg.Pool, stations: list[GeodnetStation]) -> int:
    """Insert or update rows with ``id = geodnet:<name>``. Returns rows written."""
    if not stations:
        return 0
    count = 0
    async with pool.acquire() as conn, conn.transaction():
        for st in stations:
            wkt = f"SRID=4326;POINT({st.longitude} {st.latitude})"
            active = st.is_active_for_ingest
            try:
                await conn.execute(
                    """
                        INSERT INTO geodnet_nodes (
                            id,
                            name,
                            active,
                            geom,
                            ingest_source,
                            station_status,
                            synced_at
                        )
                        VALUES (
                            $1,
                            $2,
                            $3,
                            ST_GeogFromText($4),
                            'geodnet_rtk_api',
                            $5,
                            now()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            active = EXCLUDED.active,
                            geom = EXCLUDED.geom,
                            ingest_source = EXCLUDED.ingest_source,
                            station_status = EXCLUDED.station_status,
                            synced_at = EXCLUDED.synced_at
                        """,
                    st.node_id,
                    st.name,
                    active,
                    wkt,
                    st.status,
                )
                count += 1
            except asyncpg.UndefinedColumnError:
                log.warning(
                    "geodnet_nodes missing ingest columns; run Alembic upgrade (20260517_0003)"
                )
                raise
    return count


async def sync_geodnet_stations_from_settings(pool: asyncpg.Pool, settings: Settings) -> int:
    """Fetch from RTK API and upsert. Requires enterprise ``appId`` / ``appKey``."""
    app_id = settings.geodnet_rtk_app_id
    app_key = settings.geodnet_rtk_app_key
    if not app_id or not app_key:
        raise RuntimeError(
            "GEODNET_RTK_APP_ID and GEODNET_RTK_APP_KEY must be set for station sync"
        )
    stations = await fetch_geodnet_station_list(
        api_base=settings.geodnet_rtk_api_base,
        app_id=app_id,
        app_key=app_key,
        region=settings.geodnet_rtk_station_region,
    )
    log.info("geodnet station list fetched count=%s", len(stations))
    return await upsert_geodnet_stations(pool, stations)
