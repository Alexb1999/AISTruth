from __future__ import annotations

from datetime import UTC, datetime

from aistruth_core.adapters.spire import SpireAisSource


def test_spire_row_to_report_normalizes_common_shape() -> None:
    report = SpireAisSource._row_to_report(
        {
            "mmsi": 257000000,
            "last_known_position": {
                "timestamp": "2026-01-01T00:00:00Z",
                "latitude": 60.0,
                "longitude": 5.0,
            },
        }
    )

    assert report.mmsi == 257000000
    assert report.t == datetime(2026, 1, 1, tzinfo=UTC)
    assert report.lat == 60.0
    assert report.lon == 5.0
