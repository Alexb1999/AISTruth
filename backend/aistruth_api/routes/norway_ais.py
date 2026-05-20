"""Norwegian open AIS (BarentsWatch) — Phase 1 engine-development feed."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.rate_limit import limiter
from aistruth_api.schemas import NorwayPoint, NorwayVesselSnippet
from aistruth_api.security import require_barentswatch_tenant
from aistruth_core.barentswatch import ais_position_from_combined_row, reports_from_track_rows

router = APIRouter(tags=["ais-norway"], dependencies=[Depends(require_barentswatch_tenant)])


def _require_barentswatch_credentials(settings: Settings) -> tuple[str, str]:
    cid = settings.barentswatch_client_id
    sec = settings.barentswatch_client_secret
    if not cid or not sec:
        raise HTTPException(
            status_code=503,
            detail=(
                "BarentsWatch is not configured. Set BARENTSWATCH_CLIENT_ID and "
                "BARENTSWATCH_CLIENT_SECRET (register at barentswatch.no, create API client "
                "with scope `ais`). See docs/integrations/barentswatch-ais.md."
            ),
        )
    return cid, sec


def _snippet_from_latest_row(row: dict[str, Any]) -> NorwayVesselSnippet | None:
    try:
        r = ais_position_from_combined_row(row)
    except ValueError:
        return None
    raw_name = row.get("name")
    name: str | None = (
        None if raw_name is None or raw_name == "" else (str(raw_name).strip() or None)
    )
    return NorwayVesselSnippet(
        mmsi=r.mmsi,
        lat=r.lat,
        lon=r.lon,
        time=r.t.isoformat(),
        name=name,
    )


@router.get("/ais/norway/vessels", response_model=list[NorwayVesselSnippet])
@limiter.limit("10/minute")
async def norway_latest_vessel_pick_list(
    request: Request,
    limit: int = Query(
        default=40,
        ge=1,
        le=200,
        description="Max vessels to return (subset of live feed).",
    ),
    settings: Settings = Depends(get_settings),
) -> list[NorwayVesselSnippet]:
    """Return recent vessels from BarentsWatch **GET** ``/v1/latest/combined`` for MMSI picking.

    Validation only needs an MMSI; this avoids manually looking up IDs. Upstream returns
    thousands of rows — we return the first ``limit`` successfully parsed rows.
    """
    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_latest_all_combined_cached(
            token,
            ttl_seconds=settings.vessel_list_cache_ttl_seconds,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=barentswatch_client.format_upstream_http_error(e),
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    out: list[NorwayVesselSnippet] = []
    for row in rows:
        if len(out) >= limit:
            break
        snip = _snippet_from_latest_row(row)
        if snip is not None:
            out.append(snip)
    return out


@router.get("/ais/norway/track/{mmsi}", response_model=list[NorwayPoint])
async def norway_track_last_24h(
    mmsi: int,
    settings: Settings = Depends(get_settings),
) -> list[NorwayPoint]:
    """Return parsed AIS positions (last 24h) for one MMSI inside Norwegian open-data area."""
    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_track_last_24h(token, mmsi)
        reports = reports_from_track_rows(rows)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=barentswatch_client.format_upstream_http_error(e),
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    return [
        NorwayPoint(
            mmsi=r.mmsi,
            time=r.t.isoformat(),
            lat=r.lat,
            lon=r.lon,
        )
        for r in reports
    ]


@router.get("/ais/norway/latest", response_model=list[NorwayPoint])
async def norway_latest_positions(
    mmsi: list[int] = Query(default_factory=list, description="One or more MMSI to query"),
    settings: Settings = Depends(get_settings),
) -> list[NorwayPoint]:
    """Latest combined snapshot for the given MMSI list (BarentsWatch POST /latest/combined)."""
    if not mmsi:
        raise HTTPException(status_code=400, detail="Provide at least one mmsi query parameter")
    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_latest_positions(token, mmsi)
        reports = [ais_position_from_combined_row(row) for row in rows]
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=barentswatch_client.format_upstream_http_error(e),
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    return [
        NorwayPoint(
            mmsi=r.mmsi,
            time=r.t.isoformat(),
            lat=r.lat,
            lon=r.lon,
        )
        for r in reports
    ]
