"""Coarse motion checks on AIS position time series (MVP heuristics before GEODNET fusion)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from aistruth_core.ais_adapter import AisPositionReport

# Earth radius in nautical miles (mean sphere approximation).
_R_EARTH_NM = 3440.065


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in nautical miles between two WGS84 points."""
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(h)))
    return _R_EARTH_NM * c


def implied_speed_knots(a: AisPositionReport, b: AisPositionReport) -> float | None:
    """Average speed in knots implied by straight-line distance / elapsed time."""
    dt_s = (b.t - a.t).total_seconds()
    if dt_s <= 0:
        return None
    nm = haversine_nm(a.lat, a.lon, b.lat, b.lon)
    hours = dt_s / 3600.0
    return nm / hours


@dataclass(frozen=True)
class TrackHeuristicResult:
    flags: list[str]
    max_implied_speed_knots: float | None
    confidence_score: int


def analyze_track_motion(reports: list[AisPositionReport]) -> TrackHeuristicResult:
    """Return flags and a coarse 0–100 score from implied speeds between consecutive fixes."""
    if len(reports) < 2:
        return TrackHeuristicResult(
            flags=["insufficient_samples"],
            max_implied_speed_knots=None,
            confidence_score=50,
        )

    ordered = sorted(reports, key=lambda r: r.t)
    max_speed: float | None = None
    flags: list[str] = []

    for prev, cur in zip(ordered, ordered[1:], strict=False):
        spd = implied_speed_knots(prev, cur)
        if spd is None:
            flags.append("non_monotonic_or_zero_dt")
            continue
        max_speed = spd if max_speed is None else max(max_speed, spd)
        if spd > 60:
            flags.append("implausible_speed_over_60kt")
        elif spd > 45:
            flags.append("high_speed_over_45kt")

    # De-duplicate while preserving order
    seen: set[str] = set()
    uniq_flags: list[str] = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            uniq_flags.append(f)

    score = 85
    if "implausible_speed_over_60kt" in uniq_flags:
        score -= 40
    if "high_speed_over_45kt" in uniq_flags:
        score -= 15
    if "insufficient_samples" in uniq_flags:
        score = 50
    if "non_monotonic_or_zero_dt" in uniq_flags:
        score -= 10
    score = max(0, min(100, score))

    return TrackHeuristicResult(
        flags=uniq_flags,
        max_implied_speed_knots=max_speed,
        confidence_score=score,
    )


def filter_reports_by_window(
    reports: list[AisPositionReport],
    time_from: datetime | None,
    time_to: datetime | None,
) -> list[AisPositionReport]:
    """Filter to UTC-aware window inclusive of bounds when provided."""
    out: list[AisPositionReport] = []
    for r in reports:
        t = r.t.astimezone(timezone.utc)
        if time_from is not None and t < time_from.astimezone(timezone.utc):
            continue
        if time_to is not None and t > time_to.astimezone(timezone.utc):
            continue
        out.append(r)
    return out
