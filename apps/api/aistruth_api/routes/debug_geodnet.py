"""Development endpoints for GEODNET NTRIP connectivity checks."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from aistruth_api.config import Settings, get_settings
from aistruth_core.nmea_gga import build_gpgga
from aistruth_core.ntrip_probe import run_ntrip_probe

router = APIRouter(tags=["debug-geodnet"])
log = logging.getLogger(__name__)


def _geodnet_ntrip_params(settings: Settings) -> tuple[str, str, str, int, str, float, float] | None:
    user = settings.geodnet_ntrip_user
    password = settings.geodnet_ntrip_password
    if not user or not password:
        return None
    host = settings.geodnet_ntrip_host or "rtk.geodnet.com"
    port = int(settings.geodnet_ntrip_port or 2101)
    mount = settings.geodnet_ntrip_mount or "AUTO"
    lat = float(settings.geodnet_smoke_lat)
    lon = float(settings.geodnet_smoke_lon)
    return user, password, host, port, mount, lat, lon


@router.get("/debug/geodnet-ntrip")
async def geodnet_ntrip_debug(
    seconds: float = Query(default=5.0, ge=1.0, le=15.0),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Open an NTRIP session, send periodic GGA at ``GEODNET_SMOKE_*``, return RTCM telemetry.

    Intended for local/dev verification only; do not expose publicly without auth.
    """
    params = _geodnet_ntrip_params(settings)
    if params is None:
        raise HTTPException(
            status_code=503,
            detail="GEODNET NTRIP not configured. Set GEODNET_NTRIP_USER and GEODNET_NTRIP_PASSWORD.",
        )
    user, password, host, port, mount, lat, lon = params

    def gga_factory() -> bytes:
        t = time.gmtime()
        hhmmss = f"{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}.00"
        return build_gpgga(lat, lon, utc_hhmmss=hhmmss)

    result = await run_ntrip_probe(
        host=host,
        port=port,
        mount=mount,
        user=user,
        password=password,
        gga_factory=gga_factory,
        seconds=seconds,
        gga_lat=lat,
        gga_lon=lon,
    )
    payload = asdict(result)
    log.info(
        "geodnet_ntrip_probe host=%s mount=%s ok=%s bytes=%s frames=%s",
        host,
        mount,
        result.ok,
        result.bytes_total,
        result.rtcm_frame_count,
    )
    return payload
