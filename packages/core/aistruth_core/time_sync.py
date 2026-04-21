"""Gap 1 prototype: align AIS track samples to a correction epoch (linear interpolation).

MVP uses geodetic lat/lon linear interpolation between bracketing samples. Documented
limitation: short baselines are acceptable; for long baselines or high dynamics, swap
for great-circle / Kalman propagation without changing call sites.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PositionSample:
    """Single AIS (or derived) position in time."""

    t: datetime
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if self.t.tzinfo is None:
            raise ValueError("PositionSample.t must be timezone-aware (use UTC).")


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("target_t must be timezone-aware (use UTC).")
    return dt.astimezone(timezone.utc)


def interpolate_position_at(
    samples: list[PositionSample],
    target_t: datetime,
) -> tuple[float, float, str]:
    """Return (lat, lon, method) at ``target_t`` using linear interpolation on lat/lon.

    * If ``target_t`` equals a sample time, returns that sample.
    * If ``target_t`` is before the first or after the last sample, raises ``ValueError``.
    * Requires at least two samples and strictly non-decreasing times.

    Returns a ``method`` string for explainability (e.g. ``linear_latlon``).
    """
    if len(samples) < 2:
        raise ValueError("Need at least two samples for interpolation.")
    target_t = _ensure_utc(target_t)
    times = [_ensure_utc(s.t) for s in samples]
    for i in range(1, len(times)):
        if times[i] < times[i - 1]:
            raise ValueError("samples must be ordered by non-decreasing t.")

    if target_t < times[0] or target_t > times[-1]:
        raise ValueError("target_t must lie within [first_sample.t, last_sample.t].")

    idx = bisect_left(times, target_t)
    if idx == 0 and times[0] == target_t:
        s0 = samples[0]
        return (s0.lat, s0.lon, "exact_sample")
    if idx > 0 and times[idx - 1] == target_t:
        s = samples[idx - 1]
        return (s.lat, s.lon, "exact_sample")

    # idx is insertion point; bracket is [idx-1, idx]
    lo, hi = samples[idx - 1], samples[idx]
    t0, t1 = _ensure_utc(lo.t), _ensure_utc(hi.t)
    if t1 == t0:
        raise ValueError("Duplicate timestamps in consecutive samples.")
    alpha = (target_t - t0).total_seconds() / (t1 - t0).total_seconds()
    lat = lo.lat + alpha * (hi.lat - lo.lat)
    lon = lo.lon + alpha * (hi.lon - lo.lon)
    return (lat, lon, "linear_latlon")
