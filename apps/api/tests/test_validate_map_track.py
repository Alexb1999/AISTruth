from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aistruth_api.routes.validate import _map_track_points_for_api
from aistruth_core.ais_adapter import AisPositionReport


def test_map_track_points_keeps_small_tracks_intact() -> None:
    reports = [
        AisPositionReport(mmsi=1, t=datetime(2026, 1, 1, i, tzinfo=UTC), lat=float(i), lon=1.0)
        for i in range(3)
    ]
    pts = _map_track_points_for_api(reports, max_points=400)
    assert len(pts) == 3
    assert [p["lat"] for p in pts] == [0.0, 1.0, 2.0]


def test_map_track_points_downsamples_long_tracks() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    reports = [
        AisPositionReport(
            mmsi=1,
            t=base + timedelta(minutes=i),
            lat=float(i),
            lon=0.0,
        )
        for i in range(1000)
    ]
    pts = _map_track_points_for_api(reports, max_points=10)
    assert len(pts) == 10
    assert pts[0]["lat"] == 0.0
    assert pts[-1]["lat"] == 999.0
