"""Resolve AIS tracks from tenant or deployment settings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import HTTPException

from aistruth_api.config import Settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.tenants import TenantRecord
from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.adapters.file_replay import FileReplayAisSource
from aistruth_core.adapters.spire import SpireAisSource
from aistruth_core.barentswatch import reports_from_track_rows


@dataclass(frozen=True)
class AisFetchResult:
    reports: list[AisPositionReport]
    source: str


def effective_ais_source(settings: Settings, tenant: TenantRecord | None) -> str:
    if tenant is not None and tenant.ais_source:
        return tenant.ais_source.strip().lower()
    return settings.ais_source.strip().lower()


def _effective_ais_source(settings: Settings, tenant: TenantRecord | None) -> str:
    return effective_ais_source(settings, tenant)


async def fetch_ais_reports(
    *,
    mmsi: int,
    settings: Settings,
    tenant: TenantRecord | None,
) -> AisFetchResult:
    source = _effective_ais_source(settings, tenant)
    if source == "file":
        return await _fetch_file_replay(mmsi, settings, tenant)
    if source == "spire":
        return await _fetch_spire(mmsi, settings, tenant)
    if source == "barentswatch":
        return await _fetch_barentswatch(mmsi, settings)
    raise HTTPException(status_code=503, detail=f"Unsupported AIS source: {source}")


async def _fetch_barentswatch(mmsi: int, settings: Settings) -> AisFetchResult:
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
    return AisFetchResult(reports=reports, source="barentswatch_historic_track_last_24h")


async def _fetch_file_replay(
    mmsi: int,
    settings: Settings,
    tenant: TenantRecord | None,
) -> AisFetchResult:
    path_str = (tenant.file_replay_path if tenant else None) or settings.file_replay_path
    if not path_str:
        raise HTTPException(
            status_code=503,
            detail="File replay AIS source requires FILE_REPLAY_PATH or tenant file_replay_path.",
        )
    path = Path(path_str)
    if not path.is_file():
        raise HTTPException(status_code=503, detail=f"File replay path not found: {path}")
    reports = await FileReplayAisSource(path).fetch_reports_for_mmsi(mmsi)
    if not reports:
        raise HTTPException(status_code=404, detail="No AIS points for MMSI in replay file")
    return AisFetchResult(reports=reports, source=f"file_replay:{path.name}")


async def _fetch_spire(
    mmsi: int,
    settings: Settings,
    tenant: TenantRecord | None,
) -> AisFetchResult:
    api_key = (tenant.spire_api_key if tenant else None) or settings.spire_api_key
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Spire BYOK requires SPIRE_API_KEY or tenant spire_api_key.",
        )
    source = SpireAisSource(api_key=api_key, mmsi=[mmsi], base_url=settings.spire_base_url)
    try:
        reports = await source.fetch_reports_for_mmsi(mmsi)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="No AIS track for MMSI in Spire") from e
        raise HTTPException(status_code=502, detail=f"Spire AIS request failed: {e}") from e
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail="Spire AIS request failed") from e
    finally:
        await source.aclose()
    if not reports:
        raise HTTPException(status_code=404, detail="No AIS points for MMSI from Spire")
    return AisFetchResult(reports=reports, source="spire_byok")
