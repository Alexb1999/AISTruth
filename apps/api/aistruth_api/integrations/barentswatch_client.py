"""OAuth2 client_credentials + AIS REST calls for BarentsWatch (Norwegian open AIS).

Docs: https://developer.barentswatch.no/docs/AIS/live-ais-api/
"""

from __future__ import annotations

from typing import Any

import httpx

TOKEN_URL = "https://id.barentswatch.no/connect/token"
LIVE_LATEST = "https://live.ais.barentswatch.no/v1/latest/combined"
HISTORIC_TRACK = "https://historic.ais.barentswatch.no/v1/historic/trackslast24hours"


async def fetch_access_token(client_id: str, client_secret: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "ais",
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    token = payload.get("access_token")
    if not isinstance(token, str):
        raise RuntimeError("Token response missing access_token")
    return token


async def fetch_latest_positions(token: str, mmsi_list: list[int]) -> list[dict[str, Any]]:
    """POST latest combined for specific MMSIs (see BarentsWatch examples)."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
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


async def fetch_track_last_24h(token: str, mmsi: int) -> list[dict[str, Any]]:
    """GET historic positions for one vessel over the last 24 hours."""
    url = f"{HISTORIC_TRACK}/{mmsi}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected track payload type: {type(data)}")
    return [row for row in data if isinstance(row, dict)]
