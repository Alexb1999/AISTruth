"""Scoring constants shared by API evidence and persistence."""

from __future__ import annotations

import math

RULES_VERSION = "0.2.0-alpha"


def geodnet_baseline_confidence_delta(baseline_m: float | None) -> int:
    """Integer adjustment to motion score from AIS→nearest GEODNET node distance (meters).

    Closer references add a modest boost; very long baselines nudge the score down so the
    headline number reflects station geometry context, not only implied-speed heuristics.
    """
    if baseline_m is None:
        return 0
    if not math.isfinite(baseline_m) or baseline_m < 0:
        return 0
    km = baseline_m / 1000.0
    if km <= 10:
        return 14
    if km <= 25:
        return 10
    if km <= 50:
        return 5
    if km <= 80:
        return 0
    if km <= 120:
        return -6
    if km <= 200:
        return -12
    if km <= 350:
        return -17
    return -22


def combine_motion_and_geodnet_baseline(motion_score: int, baseline_m: float | None) -> int:
    """Return 0–100 confidence with motion heuristics plus optional GEODNET baseline context."""
    total = motion_score + geodnet_baseline_confidence_delta(baseline_m)
    return max(0, min(100, total))
