from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import httpx

from aistruth_core.ais_adapter import AisPositionReport


class SpireAisSource:
    """Spire-shaped BYOK AIS adapter.

    This adapter is intentionally thin: customers provide their own API key and entitlement,
    while AISTruth normalizes returned positions into the shared `AisSource` protocol.
    """

    def __init__(
        self,
        *,
        api_key: str,
        mmsi: list[int],
        base_url: str = "https://api.spire.com",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.mmsi = mmsi
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=60.0)
        self._owns_client = client is None

    async def __aiter__(self) -> AsyncIterator[AisPositionReport]:
        rows = await self.fetch_latest_positions()
        for row in rows:
            yield self._row_to_report(row)

    async def aclose(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def fetch_latest_positions(self) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.base_url}/ais/vessels",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"mmsi": ",".join(str(value) for value in self.mmsi)},
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            values = data.get("data") or data.get("vessels") or data.get("results")
            if isinstance(values, list):
                return [row for row in values if isinstance(row, dict)]
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        raise RuntimeError(f"Unexpected Spire AIS payload type: {type(data)}")

    @staticmethod
    def _row_to_report(row: dict[str, Any]) -> AisPositionReport:
        raw_position = row.get("last_known_position")
        position = raw_position if isinstance(raw_position, dict) else row
        timestamp = (
            position.get("timestamp")
            or position.get("time")
            or position.get("msgtime")
            or datetime.now(UTC).isoformat()
        )
        return AisPositionReport(
            mmsi=int(row.get("mmsi") or position["mmsi"]),
            t=datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).astimezone(UTC),
            lat=float(position.get("latitude") or position["lat"]),
            lon=float(position.get("longitude") or position["lon"]),
        )
