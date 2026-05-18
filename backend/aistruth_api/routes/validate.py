"""Prototype validation endpoint."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import asyncpg
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import TypeAdapter

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.rate_limit import limiter
from aistruth_api.schemas import (
    BulkValidateRequest,
    BulkValidateResponse,
    BulkValidateResult,
    ValidateEvidence,
    ValidateResponse,
    ValidateWindow,
    ValidationRunRecord,
)
from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.barentswatch import reports_from_track_rows
from aistruth_core.fusion import RtkFusionEngine
from aistruth_core.nmea_gga import build_gpgga
from aistruth_core.ntrip_probe import run_ntrip_probe
from aistruth_core.scoring import RULES_VERSION, combine_motion_and_geodnet_baseline
from aistruth_core.spoofing import analyze_spoofing
from aistruth_core.track_heuristics import analyze_track_motion, filter_reports_by_window

router = APIRouter(tags=["validate"])
log = logging.getLogger(__name__)
history_adapter = TypeAdapter(list[ValidationRunRecord])

_MAX_MAP_TRACK_POINTS = 400


def _map_track_points_for_api(
    reports: list[AisPositionReport],
    max_points: int = _MAX_MAP_TRACK_POINTS,
) -> list[dict[str, str | float]]:
    """Return time-sorted fixes for the dashboard; downsample long tracks."""
    if not reports:
        return []
    sorted_r = sorted(reports, key=lambda r: r.t)
    n = len(sorted_r)
    if n <= max_points:
        return [{"lat": r.lat, "lon": r.lon, "time": r.t.isoformat()} for r in sorted_r]
    out: list[dict[str, str | float]] = []
    denom = max_points - 1 if max_points > 1 else 1
    for i in range(max_points):
        idx = min(int(i * (n - 1) // denom), n - 1)
        r = sorted_r[idx]
        out.append({"lat": r.lat, "lon": r.lon, "time": r.t.isoformat()})
    return out


def _jsonb_to_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        if isinstance(decoded, dict):
            return decoded
    return {}


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


def _http_error_detail(exc: HTTPException) -> str:
    return exc.detail if isinstance(exc.detail, str) else str(exc.detail)


async def _persist_validation_run(
    request: Request,
    response: ValidateResponse,
) -> None:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return
    run_id = uuid4()
    evidence = response.evidence.model_dump(mode="json")
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO validation_runs (
                    id,
                    mmsi,
                    window_from,
                    window_to,
                    confidence_score,
                    flags,
                    evidence,
                    rules_version,
                    nearest_node_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9)
                """,
                run_id,
                response.mmsi,
                datetime.fromisoformat(response.window.from_),
                datetime.fromisoformat(response.window.to),
                response.confidence_score,
                response.flags,
                response.evidence.model_dump_json(),
                str(evidence.get("rules_version") or RULES_VERSION),
                response.evidence.nearest_node_id,
            )
        except asyncpg.UndefinedTableError:
            log.warning("validation_runs table missing; run Alembic migrations")


@router.post("/validate/bulk", response_model=BulkValidateResponse)
@limiter.limit("10/minute")
async def validate_bulk(
    request: Request,
    body: BulkValidateRequest,
    settings: Settings = Depends(get_settings),
) -> BulkValidateResponse:
    results: list[BulkValidateResult] = []
    for mmsi in body.mmsi:
        try:
            result = await validate_mmsi(
                request=request,
                mmsi=mmsi,
                time_from=body.from_,
                time_to=body.to,
                geodnet_probe=False,
                fusion=body.fusion,
                geodnet_probe_seconds=4.0,
                settings=settings,
            )
            results.append(BulkValidateResult(mmsi=mmsi, result=result))
        except HTTPException as exc:
            results.append(
                BulkValidateResult(
                    mmsi=mmsi,
                    error=_http_error_detail(exc),
                    status_code=exc.status_code,
                )
            )
    return BulkValidateResponse(results=results)


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
    fusion: bool = Query(
        default=False,
        description="If true, attach rtk_v1 fusion evidence from a short correction probe.",
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
            detail=barentswatch_client.format_upstream_http_error(e),
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Upstream AIS request failed") from e

    filtered = filter_reports_by_window(reports, time_from, time_to)
    if not filtered:
        raise HTTPException(status_code=404, detail="No AIS points in requested time window")

    motion = analyze_track_motion(filtered)
    spoofing_findings = analyze_spoofing(filtered)
    last = max(filtered, key=lambda r: r.t)

    nearest_id: str | None = None
    baseline_m: float | None = None
    nearest_node: dict[str, Any] | None = None
    geodnet_map_nodes: list[dict[str, Any]] = []
    pool = getattr(request.app.state, "db_pool", None)
    if pool is not None:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id,
                       name,
                       ST_Y(geom::geometry) AS lat,
                       ST_X(geom::geometry) AS lon,
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
                nearest_node = {
                    "id": nearest_id,
                    "name": str(row["name"]),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "distance_m": baseline_m,
                }

            lats = [r.lat for r in filtered]
            lons = [r.lon for r in filtered]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            pad_deg = 0.85
            env_min_lon = max(-180.0, min_lon - pad_deg)
            env_min_lat = max(-90.0, min_lat - pad_deg)
            env_max_lon = min(180.0, max_lon + pad_deg)
            env_max_lat = min(90.0, max_lat + pad_deg)
            map_rows = await conn.fetch(
                """
                SELECT id,
                       name,
                       ST_Y(geom::geometry) AS lat,
                       ST_X(geom::geometry) AS lon
                FROM geodnet_nodes
                WHERE active
                  AND geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
                ORDER BY id
                LIMIT 350
                """,
                env_min_lon,
                env_min_lat,
                env_max_lon,
                env_max_lat,
            )
            geodnet_map_nodes = [
                {
                    "id": str(r["id"]),
                    "name": str(r["name"]),
                    "lat": float(r["lat"]),
                    "lon": float(r["lon"]),
                }
                for r in map_rows
            ]

    window_start = min(r.t for r in filtered).isoformat()
    window_end = max(r.t for r in filtered).isoformat()
    map_track_points = _map_track_points_for_api(filtered)

    evidence: dict[str, Any] = {
        "track_points": len(filtered),
        "source": "barentswatch_historic_track_last_24h",
        "rules_version": RULES_VERSION,
        "nearest_node_id": nearest_id,
        "baseline_m": baseline_m,
        "nearest_node": nearest_node,
        "map_track_points": map_track_points,
        "geodnet_map_nodes": geodnet_map_nodes,
        "max_implied_speed_knots": motion.max_implied_speed_knots,
        "time_align_method": "slerp_v1",
        "spoofing_findings": [finding.to_dict() for finding in spoofing_findings],
    }

    if geodnet_probe or fusion:
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
            if fusion:
                evidence["time_align_method"] = "rtk_v1"
                received_at = datetime.now(UTC) if probe.bytes_total > 0 else None
                evidence["fusion_result"] = (
                    RtkFusionEngine()
                    .build_result(
                        latest_ais_lat=plat,
                        latest_ais_lon=plon,
                        baseline_m=baseline_m,
                        correction_received_at=received_at,
                    )
                    .to_dict()
                )
            log.info(
                "validate geodnet_probe mmsi=%s ok=%s bytes=%s frames=%s",
                mmsi,
                probe.ok,
                probe.bytes_total,
                probe.rtcm_frame_count,
            )
        except Exception as e:  # pragma: no cover - defensive
            evidence["geodnet_ntrip_probe"] = {
                "ok": False,
                "host": host,
                "port": port,
                "mount": mount,
                "gga_lat": plat,
                "gga_lon": plon,
                "error": repr(e),
            }
            log.warning("validate geodnet_probe failed mmsi=%s err=%s", mmsi, e)

    confidence_score = combine_motion_and_geodnet_baseline(motion.confidence_score, baseline_m)

    response = ValidateResponse(
        mmsi=mmsi,
        window=ValidateWindow.model_validate({"from": window_start, "to": window_end}),
        confidence_score=confidence_score,
        flags=motion.flags,
        evidence=ValidateEvidence(**evidence),
    )
    await _persist_validation_run(request, response)
    return response


@router.get("/validate/{mmsi}/history", response_model=list[ValidationRunRecord])
async def validation_history(
    request: Request,
    mmsi: int,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ValidationRunRecord]:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="DATABASE_URL not set or pool unavailable")
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id::text,
                mmsi,
                requested_at,
                window_from,
                window_to,
                confidence_score,
                flags,
                evidence
            FROM validation_runs
            WHERE mmsi = $1
            ORDER BY requested_at DESC
            LIMIT $2
            """,
            mmsi,
            limit,
        )
    records = [
        {
            "id": row["id"],
            "mmsi": row["mmsi"],
            "requested_at": row["requested_at"],
            "window": {"from": row["window_from"].isoformat(), "to": row["window_to"].isoformat()},
            "confidence_score": row["confidence_score"],
            "flags": list(row["flags"]),
            "evidence": _jsonb_to_dict(row["evidence"]),
        }
        for row in rows
    ]
    return history_adapter.validate_python(records)
