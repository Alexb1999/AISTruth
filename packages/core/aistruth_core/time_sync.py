"""Gap 1 prototype: align AIS track samples to a correction epoch.

MVP uses great-circle interpolation between bracketing AIS samples. For high dynamics,
replace this with a track smoother / Kalman propagation without changing call sites.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from datetime import UTC, datetime


class ExtrapolationError(ValueError):
    """Raised when a requested epoch is outside the available track window."""


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
    return dt.astimezone(UTC)


def _normalize_lon(lon: float) -> float:
    normalized = ((lon + 180.0) % 360.0) - 180.0
    if normalized == -180.0 and lon > 0:
        return 180.0
    return normalized


def _to_unit_vector(lat: float, lon: float) -> tuple[float, float, float]:
    phi = math.radians(lat)
    lam = math.radians(lon)
    cos_phi = math.cos(phi)
    return (
        cos_phi * math.cos(lam),
        cos_phi * math.sin(lam),
        math.sin(phi),
    )


def _from_unit_vector(vec: tuple[float, float, float]) -> tuple[float, float]:
    x, y, z = vec
    hyp = math.hypot(x, y)
    lat = math.degrees(math.atan2(z, hyp))
    lon = math.degrees(math.atan2(y, x))
    return lat, _normalize_lon(lon)


def _slerp_latlon(
    start: tuple[float, float],
    end: tuple[float, float],
    alpha: float,
) -> tuple[float, float]:
    v0 = _to_unit_vector(*start)
    v1 = _to_unit_vector(*end)
    dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(v0, v1, strict=True))))
    omega = math.acos(dot)
    if omega < 1e-12:
        lat = start[0] + alpha * (end[0] - start[0])
        lon = start[1] + alpha * (_normalize_lon(end[1] - start[1]))
        return lat, _normalize_lon(lon)
    sin_omega = math.sin(omega)
    scale0 = math.sin((1.0 - alpha) * omega) / sin_omega
    scale1 = math.sin(alpha * omega) / sin_omega
    vec = (
        scale0 * v0[0] + scale1 * v1[0],
        scale0 * v0[1] + scale1 * v1[1],
        scale0 * v0[2] + scale1 * v1[2],
    )
    norm = math.sqrt(sum(component * component for component in vec))
    unit_vec = (vec[0] / norm, vec[1] / norm, vec[2] / norm)
    return _from_unit_vector(unit_vec)


def interpolate_position_at(
    samples: list[PositionSample],
    target_t: datetime,
) -> tuple[float, float, str]:
    """Return (lat, lon, method) at ``target_t`` using great-circle interpolation.

    * If ``target_t`` equals a sample time, returns that sample.
    * If ``target_t`` is before the first or after the last sample, raises ``ExtrapolationError``.
    * Requires at least two samples and strictly non-decreasing times.

    Returns a ``method`` string for explainability (e.g. ``slerp_great_circle``).
    """
    if len(samples) < 2:
        raise ValueError("Need at least two samples for interpolation.")
    target_t = _ensure_utc(target_t)
    times = [_ensure_utc(s.t) for s in samples]
    for i in range(1, len(times)):
        if times[i] < times[i - 1]:
            raise ValueError("samples must be ordered by non-decreasing t.")

    if target_t < times[0] or target_t > times[-1]:
        raise ExtrapolationError("target_t must lie within [first_sample.t, last_sample.t].")

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
    lat, lon = _slerp_latlon((lo.lat, lo.lon), (hi.lat, hi.lon), alpha)
    return (lat, lon, "slerp_great_circle")
