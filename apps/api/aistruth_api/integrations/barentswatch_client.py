"""OAuth2 client_credentials + AIS REST calls for BarentsWatch (Norwegian open AIS).

Docs: https://developer.barentswatch.no/docs/AIS/live-ais-api/
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

TOKEN_URL = "https://id.barentswatch.no/connect/token"
LIVE_LATEST = "https://live.ais.barentswatch.no/v1/latest/combined"
HISTORIC_TRACK = "https://historic.ais.barentswatch.no/v1/historic/trackslast24hours"


@dataclass
class _CachedTrack:
    expires_at: float
    rows: list[dict[str, Any]]


class BarentsWatchClient:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=60.0)
        self._owns_client = client is None
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._track_cache: dict[tuple[str, int], _CachedTrack] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2.0),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_access_token(self, client_id: str, client_secret: str) -> str:
        now = time.monotonic()
        if self._token and self._token_expires_at > now:
            return self._token
        response = await self._client.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "ais",
                "grant_type": "client_credentials",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        token = payload.get("access_token")
        if not isinstance(token, str):
            raise RuntimeError("Token response missing access_token")
        expires_in = int(payload.get("expires_in") or 3600)
        self._token = token
        self._token_expires_at = now + max(0, expires_in - 60)
        return token

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2.0),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_latest_positions(
        self,
        token: str,
        mmsi_list: list[int],
    ) -> list[dict[str, Any]]:
        response = await self._client.post(
            LIVE_LATEST,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"mmsi": mmsi_list},
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected latest/combined payload type: {type(data)}")
        return [row for row in data if isinstance(row, dict)]

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=2.0),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def fetch_track_last_24h(self, token: str, mmsi: int) -> list[dict[str, Any]]:
        url = f"{HISTORIC_TRACK}/{mmsi}"
        response = await self._client.get(url, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected track payload type: {type(data)}")
        return [row for row in data if isinstance(row, dict)]

    async def fetch_track_last_24h_cached(
        self,
        token: str,
        mmsi: int,
        *,
        ttl_seconds: int,
    ) -> list[dict[str, Any]]:
        if ttl_seconds <= 0:
            return await self.fetch_track_last_24h(token, mmsi)
        key = (token, mmsi)
        now = time.monotonic()
        cached = self._track_cache.get(key)
        if cached and cached.expires_at > now:
            return cached.rows
        rows = await self.fetch_track_last_24h(token, mmsi)
        self._track_cache[key] = _CachedTrack(expires_at=now + ttl_seconds, rows=rows)
        if len(self._track_cache) > 256:
            oldest_key = min(self._track_cache, key=lambda item: self._track_cache[item].expires_at)
            self._track_cache.pop(oldest_key, None)
        return rows


_default_client = BarentsWatchClient()


async def close_default_client() -> None:
    await _default_client.aclose()


async def fetch_access_token(client_id: str, client_secret: str) -> str:
    return await _default_client.fetch_access_token(client_id, client_secret)


async def fetch_latest_positions(token: str, mmsi_list: list[int]) -> list[dict[str, Any]]:
    """POST latest combined for specific MMSIs (see BarentsWatch examples)."""
    return await _default_client.fetch_latest_positions(token, mmsi_list)


async def fetch_track_last_24h(token: str, mmsi: int) -> list[dict[str, Any]]:
    """GET historic positions for one vessel over the last 24 hours."""
    return await _default_client.fetch_track_last_24h(token, mmsi)


async def fetch_track_last_24h_cached(
    token: str,
    mmsi: int,
    *,
    ttl_seconds: int,
) -> list[dict[str, Any]]:
    return await _default_client.fetch_track_last_24h_cached(
        token,
        mmsi,
        ttl_seconds=ttl_seconds,
    )
