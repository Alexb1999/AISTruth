from __future__ import annotations

from datetime import UTC, datetime

from aistruth_core.fusion import RtkFusionEngine


def test_fusion_engine_returns_telemetry_backed_contract() -> None:
    result = RtkFusionEngine().build_result(
        latest_ais_lat=60.0,
        latest_ais_lon=5.0,
        baseline_m=123.4,
        correction_received_at=datetime.now(UTC),
    )

    assert result.ok is True
    assert result.method == "rtk_v1"
    assert result.refined_lat == 60.0
    assert result.refined_lon == 5.0
    assert result.baseline_m == 123.4
    assert result.pdop is None
    assert result.status == "telemetry_only_rover_observations_unavailable"
