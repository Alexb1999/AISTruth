"""GEODNET RTK REST API helpers (enterprise station list, coverage).

Specification: https://github.com/geodnet/GEODNET_API/blob/main/GEODNET_RTK_API.md
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def build_geodnet_sign(params: dict[str, Any], app_key: str) -> str:
    """MD5 sign for POST body fields (excludes ``sign``; ``appKey`` is never sent).

    Keys are sorted lexicographically; each value is concatenated as ``str(value)``.
    """
    keys = sorted(k for k in params if k != "sign")
    concatenated = "".join(str(params[k]) for k in keys)
    payload = f"{concatenated}{app_key}".encode()
    return hashlib.md5(payload, usedforsecurity=False).hexdigest()


def station_list_request_body(
    *,
    app_id: str,
    app_key: str,
    time_ms: int,
    region: str | None = None,
) -> dict[str, Any]:
    """Build JSON body for ``POST .../api/v3/station/list`` including ``sign``."""
    body: dict[str, Any] = {"appId": app_id, "time": time_ms}
    if region is not None and region != "":
        body["region"] = region
    body["sign"] = build_geodnet_sign(body, app_key)
    return body


@dataclass(frozen=True)
class GeodnetStation:
    """One row from ``/api/v3/station/list`` ``data[]``."""

    name: str
    latitude: float
    longitude: float
    height_m: float | None
    status: str

    @property
    def is_active_for_ingest(self) -> bool:
        return self.status.upper() in {"ACTIVE", "ONLINE"}

    @property
    def node_id(self) -> str:
        """Primary key fragment stored in ``geodnet_nodes.id`` (namespaced)."""
        return f"geodnet:{self.name}"


def parse_station_list_response(payload: object) -> list[GeodnetStation]:
    """Parse JSON object from RTK API; raises ValueError on unexpected shape."""
    if not isinstance(payload, dict):
        raise ValueError("station list response must be a JSON object")
    code = payload.get("code")
    if code != 1000:
        msg = payload.get("msg", "unknown error")
        raise ValueError(f"GEODNET RTK API error code={code} msg={msg}")
    raw_list = payload.get("data")
    if not isinstance(raw_list, list):
        raise ValueError("station list response missing data array")
    out: list[GeodnetStation] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        lat = item.get("latitude")
        lon = item.get("longitude")
        status = item.get("status")
        if not isinstance(name, str) or not isinstance(lat, int | float):
            continue
        if not isinstance(lon, int | float):
            continue
        if not isinstance(status, str):
            status = "UNKNOWN"
        height_raw = item.get("height")
        height: float | None
        height = float(height_raw) if isinstance(height_raw, int | float) else None
        out.append(
            GeodnetStation(
                name=name,
                latitude=float(lat),
                longitude=float(lon),
                height_m=height,
                status=status,
            )
        )
    return out


def station_list_response_from_json(text: str) -> list[GeodnetStation]:
    return parse_station_list_response(json.loads(text))
