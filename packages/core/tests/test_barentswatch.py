from datetime import datetime, timezone

import pytest

from aistruth_core.barentswatch import (
    ais_position_from_combined_row,
    parse_msgtime,
    reports_from_track_rows,
)


def test_parse_msgtime_fraction_trim() -> None:
    t = parse_msgtime("2022-11-02T13:41:05.8449617+00:00")
    assert t.tzinfo == timezone.utc
    assert t.microsecond == 844961


def test_ais_position_from_row() -> None:
    row = {
        "mmsi": 259139000,
        "latitude": 63.642362,
        "longitude": 9.613247,
        "msgtime": "2022-11-02T13:57:43+00:00",
        "name": "NORDLYS",
    }
    r = ais_position_from_combined_row(row)
    assert r.mmsi == 259139000
    assert r.lat == pytest.approx(63.642362)
    assert r.lon == pytest.approx(9.613247)
    assert r.t == datetime(2022, 11, 2, 13, 57, 43, tzinfo=timezone.utc)


def test_reports_sorted_oldest_first() -> None:
    rows = [
        {"mmsi": 1, "latitude": 0.0, "longitude": 0.0, "msgtime": "2022-01-01T12:00:01+00:00"},
        {"mmsi": 1, "latitude": 0.0, "longitude": 0.0, "msgtime": "2022-01-01T12:00:00+00:00"},
    ]
    out = reports_from_track_rows(rows)
    assert out[0].t < out[1].t
