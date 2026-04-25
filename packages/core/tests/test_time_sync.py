from datetime import UTC, datetime, timedelta

import pytest

from aistruth_core.time_sync import ExtrapolationError, PositionSample, interpolate_position_at


def _t(base: datetime, seconds: float) -> datetime:
    return base + timedelta(seconds=seconds)


def test_interpolate_midpoint() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    s0 = PositionSample(base, 0.0, 0.0)
    s1 = PositionSample(_t(base, 60), 0.0, 10.0)
    lat, lon, method = interpolate_position_at([s0, s1], _t(base, 30))
    assert method == "slerp_great_circle"
    assert lat == pytest.approx(0.0)
    assert lon == pytest.approx(5.0)


def test_interpolate_crosses_antimeridian() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    s0 = PositionSample(base, 0.0, 179.0)
    s1 = PositionSample(_t(base, 60), 0.0, -179.0)
    lat, lon, method = interpolate_position_at([s0, s1], _t(base, 30))

    assert method == "slerp_great_circle"
    assert lat == pytest.approx(0.0)
    assert abs(abs(lon) - 180.0) < 1e-9


def test_exact_sample() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    s0 = PositionSample(base, 1.0, 2.0)
    s1 = PositionSample(_t(base, 10), 3.0, 4.0)
    lat, lon, method = interpolate_position_at([s0, s1], base)
    assert method == "exact_sample"
    assert lat == 1.0 and lon == 2.0


def test_out_of_range_raises() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    samples = [PositionSample(base, 0, 0), PositionSample(_t(base, 10), 1, 1)]
    with pytest.raises(ExtrapolationError):
        interpolate_position_at(samples, _t(base, -1))
    with pytest.raises(ExtrapolationError):
        interpolate_position_at(samples, _t(base, 11))


def test_naive_datetime_rejected() -> None:
    base = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    samples = [PositionSample(base, 0, 0), PositionSample(_t(base, 10), 1, 1)]
    naive = datetime(2025, 1, 1, 12, 0, 5)
    with pytest.raises(ValueError, match="timezone-aware"):
        interpolate_position_at(samples, naive)
