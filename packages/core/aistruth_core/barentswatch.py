"""Parse Norwegian Coastal Administration / BarentsWatch AIS JSON into :class:`AisPositionReport`.

Official docs: https://developer.barentswatch.no/docs/AIS/examples/
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from aistruth_core.ais_adapter import AisPositionReport

# BarentsWatch occasionally emits sub-microsecond precision; trim beyond 6 fractional digits.
_FRACTION_TRIM = re.compile(r"(\.\d{6})\d+(?=[+-]|Z)")


def parse_msgtime(value: str) -> datetime:
    """Parse ``msgtime`` from the AIS API into aware UTC :class:`~datetime.datetime`."""
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    s = _FRACTION_TRIM.sub(r"\1", s)
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def ais_position_from_combined_row(row: dict[str, Any]) -> AisPositionReport:
    """Build a report from a ``/v1/latest/combined`` or historic track row dict."""
    try:
        mmsi = int(row["mmsi"])
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        t = parse_msgtime(str(row["msgtime"]))
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Invalid BarentsWatch AIS row: {row!r}") from e
    return AisPositionReport(mmsi=mmsi, t=t, lat=lat, lon=lon)


def reports_from_track_rows(rows: list[dict[str, Any]]) -> list[AisPositionReport]:
    """Convert historic/live track JSON array to reports sorted oldest-first."""
    reports = [ais_position_from_combined_row(r) for r in rows]
    return sorted(reports, key=lambda r: r.t)
