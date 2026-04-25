from datetime import UTC, datetime, timedelta

from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.track_heuristics import (
    analyze_track_motion,
    filter_reports_by_window,
    haversine_nm,
    implied_speed_knots,
)


def test_haversine_one_degree_latitude() -> None:
    nm = haversine_nm(0.0, 0.0, 1.0, 0.0)
    assert 59.0 < nm < 61.0


def test_implied_speed_two_points() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    a = AisPositionReport(123, base, 0.0, 0.0)
    b = AisPositionReport(123, base + timedelta(hours=1), 1.0, 0.0)
    spd = implied_speed_knots(a, b)
    assert spd is not None
    assert 55.0 < spd < 65.0


def test_analyze_flags_high_speed() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    r0 = AisPositionReport(1, base, 0.0, 0.0)
    r1 = AisPositionReport(1, base + timedelta(minutes=1), 2.0, 0.0)  # huge implied speed
    res = analyze_track_motion([r0, r1])
    assert res.max_implied_speed_knots is not None
    assert res.max_implied_speed_knots > 60
    assert "implausible_speed_over_60kt" in res.flags


def test_filter_window() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    reps = [
        AisPositionReport(1, base, 0, 0),
        AisPositionReport(1, base + timedelta(hours=2), 1, 1),
    ]
    f = filter_reports_by_window(reps, base + timedelta(hours=1), base + timedelta(hours=3))
    assert len(f) == 1
    assert f[0].t == base + timedelta(hours=2)
