from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.spoofing import (
    analyze_spoofing,
    mmsi_swap_detector,
    position_freeze_detector,
)


def test_analyze_spoofing_flags_impossible_jump() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    reports = [
        AisPositionReport(1, base, 0.0, 0.0),
        AisPositionReport(1, base + timedelta(minutes=1), 2.0, 0.0),
    ]

    findings = analyze_spoofing(reports)

    assert findings[0].kind == "implausible_speed_over_60kt"
    assert findings[0].severity == "high"


def test_position_freeze_detector_flags_repeated_fix() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    reports = [AisPositionReport(1, base + timedelta(seconds=idx), 60.0, 5.0) for idx in range(3)]

    findings = position_freeze_detector(reports)

    assert len(findings) == 1
    assert findings[0].kind == "position_freeze"
    assert findings[0].evidence["count"] == 3


def test_mmsi_swap_detector_flags_same_position_multiple_mmsi() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    reports = [
        AisPositionReport(1, base, 60.0, 5.0),
        AisPositionReport(2, base, 60.0, 5.0),
    ]

    findings = mmsi_swap_detector(reports)

    assert len(findings) == 1
    assert findings[0].kind == "mmsi_swap_same_position"
    assert findings[0].evidence["mmsi"] == [1, 2]
