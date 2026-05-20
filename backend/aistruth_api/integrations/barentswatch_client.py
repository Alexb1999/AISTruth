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


def format_upstream_http_error(exc: httpx.HTTPStatusError) -> str:
    """Turn a BarentsWatch httpx error into a FastAPI-safe detail string for operators."""
    url = str(exc.request.url)
    status = exc.response.status_code
    body_bit = ""
    try:
        raw = (exc.response.text or "").strip().replace("\n", " ")
        if raw:
            body_bit = f" Upstream body: {raw[:240]}{'…' if len(raw) > 240 else ''}"
    except Exception:
        pass

    if "id.barentswatch.no" in url:
        return (
            f"BarentsWatch OAuth token request failed (HTTP {status}). "
            "Check BARENTSWATCH_CLIENT_ID and BARENTSWATCH_CLIENT_SECRET, scope `ais`, "
            "and quoting in backend/.env if the client id contains `@`, `:`, or spaces "
            "(see docs/integrations/barentswatch-ais.md — Token errors)."
            f"{body_bit}"
        )

    if "live.ais.barentswatch.no" in url:
        if status == 401:
            return (
                "BarentsWatch live AIS returned HTTP 401. The bearer token was rejected—usually invalid "
                "or expired client credentials, missing `ais` scope, or a MyPage client without live AIS access. "
                "Run the token + curl checks in docs/integrations/barentswatch-ais.md, then restart the API."
            )
        return f"BarentsWatch live AIS request failed (HTTP {status}).{body_bit}"

    if "historic.ais.barentswatch.no" in url:
        if status == 401:
            return (
                "BarentsWatch historic AIS returned HTTP 401 (same checks as live: credentials and `ais` scope). "
                "See docs/integrations/barentswatch-ais.md."
            )
        return f"BarentsWatch historic AIS request failed (HTTP {status}).{body_bit}"

    return f"Upstream AIS error: {status}.{body_bit}"


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
        self._latest_all_cache: _CachedTrack | None = None

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
    async def fetch_latest_all_combined(self, token: str) -> list[dict[str, Any]]:
        """GET latest AIS snapshot for all vessels (open-data feed; can be many rows)."""
        response = await self._client.get(
            LIVE_LATEST,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected latest/combined payload type: {type(data)}")
        return [row for row in data if isinstance(row, dict)]

    async def fetch_latest_all_combined_cached(
        self,
        token: str,
        *,
        ttl_seconds: int,
    ) -> list[dict[str, Any]]:
        if ttl_seconds <= 0:
            return await self.fetch_latest_all_combined(token)
        now = time.monotonic()
        cached = self._latest_all_cache
        if cached and cached.expires_at > now:
            return cached.rows
        rows = await self.fetch_latest_all_combined(token)
        self._latest_all_cache = _CachedTrack(expires_at=now + ttl_seconds, rows=rows)
        return rows

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


async def fetch_latest_all_combined(token: str) -> list[dict[str, Any]]:
    """GET combined latest positions for all vessels (BarentsWatch open AIS)."""
    return await _default_client.fetch_latest_all_combined(token)


async def fetch_latest_all_combined_cached(
    token: str,
    *,
    ttl_seconds: int,
) -> list[dict[str, Any]]:
    return await _default_client.fetch_latest_all_combined_cached(
        token,
        ttl_seconds=ttl_seconds,
    )


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
