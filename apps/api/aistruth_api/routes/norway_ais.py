"""Norwegian open AIS (BarentsWatch) — Phase 1 engine-development feed."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_core.barentswatch import ais_position_from_combined_row, reports_from_track_rows

router = APIRouter(tags=["ais-norway"])


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


@router.get("/ais/norway/track/{mmsi}")
async def norway_track_last_24h(
    mmsi: int,
    settings: Settings = Depends(get_settings),
) -> list[dict[str, object]]:
    """Return parsed AIS positions (last 24h) for one MMSI inside Norwegian open-data area."""
    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_track_last_24h(token, mmsi)
        reports = reports_from_track_rows(rows)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream AIS error: {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    return [
        {
            "mmsi": r.mmsi,
            "time": r.t.isoformat(),
            "lat": r.lat,
            "lon": r.lon,
        }
        for r in reports
    ]


@router.get("/ais/norway/latest")
async def norway_latest_positions(
    mmsi: list[int] = Query(default_factory=list, description="One or more MMSI to query"),
    settings: Settings = Depends(get_settings),
) -> list[dict[str, object]]:
    """Latest combined snapshot for the given MMSI list (BarentsWatch POST /latest/combined)."""
    if not mmsi:
        raise HTTPException(status_code=400, detail="Provide at least one mmsi query parameter")
    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_latest_positions(token, mmsi)
        reports = [ais_position_from_combined_row(row) for row in rows]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream AIS error: {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    return [
        {
            "mmsi": r.mmsi,
            "time": r.t.isoformat(),
            "lat": r.lat,
            "lon": r.lon,
        }
        for r in reports
    ]
