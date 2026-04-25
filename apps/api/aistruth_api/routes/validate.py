"""Prototype validation endpoint."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.rate_limit import limiter
from aistruth_api.schemas import ValidateEvidence, ValidateResponse, ValidateWindow
from aistruth_core.barentswatch import reports_from_track_rows
from aistruth_core.nmea_gga import build_gpgga
from aistruth_core.ntrip_probe import run_ntrip_probe
from aistruth_core.track_heuristics import analyze_track_motion, filter_reports_by_window

router = APIRouter(tags=["validate"])
log = logging.getLogger(__name__)


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


@router.get("/validate/{mmsi}", response_model=ValidateResponse)
@limiter.limit("30/minute")
async def validate_mmsi(
    request: Request,
    mmsi: int,
    time_from: datetime | None = Query(default=None, alias="from"),
    time_to: datetime | None = Query(default=None, alias="to"),
    geodnet_probe: bool = Query(
        default=False,
        description=(
            "If true, run a short GEODNET NTRIP probe; adds latency and uses the "
            "last AIS fix for GGA."
        ),
    ),
    geodnet_probe_seconds: float = Query(
        default=4.0,
        ge=1.0,
        le=10.0,
        description="NTRIP collection duration when geodnet_probe=true",
    ),
    settings: Settings = Depends(get_settings),
) -> ValidateResponse:
    """MVP validation: AIS track (BarentsWatch 24h) + implied-speed flags + optional PostGIS node.

    GEODNET / RTCM fusion is not applied yet; ``time_align_method`` documents that gap explicitly.
    Optional ``geodnet_probe`` attaches RTCM **telemetry** (bytes + RTCM message histogram) from a
    short live NTRIP session using GGA at the **latest AIS position** in the filtered window.
    """
    if time_from is not None and time_to is not None and time_from > time_to:
        raise HTTPException(status_code=400, detail="from must be <= to")

    cid, sec = _require_barentswatch_credentials(settings)
    try:
        token = await barentswatch_client.fetch_access_token(cid, sec)
        rows = await barentswatch_client.fetch_track_last_24h_cached(
            token,
            mmsi,
            ttl_seconds=settings.track_cache_ttl_seconds,
        )
        reports = reports_from_track_rows(rows)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="No AIS track for MMSI in upstream window",
            ) from e
        raise HTTPException(
            status_code=502,
            detail=f"Upstream AIS error: {e.response.status_code}",
        ) from e
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

    evidence: dict[str, Any] = {
        "track_points": len(filtered),
        "source": "barentswatch_historic_track_last_24h",
        "rules_version": "0.1.0-alpha",
        "nearest_node_id": nearest_id,
        "baseline_m": baseline_m,
        "max_implied_speed_knots": motion.max_implied_speed_knots,
        "time_align_method": "none_track_uses_native_msgtime",
    }

    if geodnet_probe:
        gu = settings.geodnet_ntrip_user
        gp = settings.geodnet_ntrip_password
        if not gu or not gp:
            raise HTTPException(
                status_code=400,
                detail=(
                    "geodnet_probe=true but GEODNET_NTRIP_USER / "
                    "GEODNET_NTRIP_PASSWORD are not set on the API."
                ),
            )
        host = settings.geodnet_ntrip_host or "rtk.geodnet.com"
        port = int(settings.geodnet_ntrip_port or 2101)
        mount = settings.geodnet_ntrip_mount or "AUTO"
        plat, plon = last.lat, last.lon

        def gga_factory() -> bytes:
            t = time.gmtime()
            hhmmss = f"{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}.00"
            return build_gpgga(plat, plon, utc_hhmmss=hhmmss)

        try:
            probe = await run_ntrip_probe(
                host=host,
                port=port,
                mount=mount,
                user=gu,
                password=gp,
                gga_factory=gga_factory,
                seconds=geodnet_probe_seconds,
                gga_lat=plat,
                gga_lon=plon,
            )
            evidence["geodnet_ntrip_probe"] = asdict(probe)
            log.info(
                "validate geodnet_probe mmsi=%s ok=%s bytes=%s frames=%s",
                mmsi,
                probe.ok,
                probe.bytes_total,
                probe.rtcm_frame_count,
            )
        except (OSError, TimeoutError) as e:  # pragma: no cover - network paths
            evidence["geodnet_ntrip_probe"] = {"ok": False, "error": repr(e)}
            log.warning("validate geodnet_probe failed mmsi=%s err=%s", mmsi, e)

    return ValidateResponse(
        mmsi=mmsi,
        window=ValidateWindow.model_validate({"from": window_start, "to": window_end}),
        confidence_score=motion.confidence_score,
        flags=motion.flags,
        evidence=ValidateEvidence(**evidence),
    )
