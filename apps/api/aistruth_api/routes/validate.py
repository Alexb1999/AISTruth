"""Prototype validation endpoint — BarentsWatch track + motion heuristics + optional nearest node."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_core.barentswatch import reports_from_track_rows
from aistruth_core.track_heuristics import analyze_track_motion, filter_reports_by_window

router = APIRouter(tags=["validate"])


def _require_barentswatch_credentials(settings: Settings) -> tuple[str, str]:
    cid = settings.barentswatch_client_id
    sec = settings.barentswatch_client_secret
    if not cid or not sec:
        raise HTTPException(
            status_code=503,
            detail=(
                "BarentsWatch is not configured. Set BARENTSWATCH_CLIENT_ID and "
                "BARENTSWATCH_CLIENT_SECRET. See docs/integrations/barentswatch-ais.md."
            ),
        )
    return cid, sec


@router.get("/validate/{mmsi}")
async def validate_mmsi(
    request: Request,
    mmsi: int,
    time_from: datetime | None = Query(default=None, alias="from"),
    time_to: datetime | None = Query(default=None, alias="to"),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """MVP validation: AIS track (BarentsWatch 24h) + implied-speed flags + optional PostGIS node.

    GEODNET / RTCM fusion is not applied yet; ``time_align_method`` documents that gap explicitly.
    """
    if time_from is not None and time_to is not None and time_from > time_to:
        raise HTTPException(status_code=400, detail="from must be <= to")

    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_track_last_24h(token, mmsi)
        reports = reports_from_track_rows(rows)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="No AIS track for MMSI in upstream window") from e
        raise HTTPException(status_code=502, detail=f"Upstream AIS error: {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    filtered = filter_reports_by_window(reports, time_from, time_to)
    if not filtered:
        raise HTTPException(status_code=404, detail="No AIS points in requested time window")

    motion = analyze_track_motion(filtered)
    last = max(filtered, key=lambda r: r.t)

    nearest_id: str | None = None
    baseline_m: float | None = None
    pool = getattr(request.app.state, "db_pool", None)
    if pool is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id,
                       ST_Distance(
                           geom,
                           ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                       ) AS dist_m
                FROM geodnet_nodes
                WHERE active
                ORDER BY geom <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                LIMIT 1
                """,
                last.lon,
                last.lat,
            )
        if row is not None:
            nearest_id = str(row["id"])
            baseline_m = float(row["dist_m"])

    window_start = min(r.t for r in filtered).isoformat()
    window_end = max(r.t for r in filtered).isoformat()

    return {
        "mmsi": mmsi,
        "window": {"from": window_start, "to": window_end},
        "confidence_score": motion.confidence_score,
        "flags": motion.flags,
        "evidence": {
            "track_points": len(filtered),
            "source": "barentswatch_historic_track_last_24h",
            "rules_version": "0.1.0-alpha",
            "nearest_node_id": nearest_id,
            "baseline_m": baseline_m,
            "max_implied_speed_knots": motion.max_implied_speed_knots,
            "time_align_method": "none_track_uses_native_msgtime",
        },
    }
