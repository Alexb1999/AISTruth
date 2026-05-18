from aistruth_core.scoring import combine_motion_and_geodnet_baseline, geodnet_baseline_confidence_delta


def test_geodnet_delta_none() -> None:
    assert geodnet_baseline_confidence_delta(None) == 0


def test_geodnet_delta_close_vs_far() -> None:
    assert geodnet_baseline_confidence_delta(5_000) == 14
    assert geodnet_baseline_confidence_delta(20_000) == 10
    assert geodnet_baseline_confidence_delta(30_000) == 5
    assert geodnet_baseline_confidence_delta(106_000) == -6
    assert geodnet_baseline_confidence_delta(500_000) == -22


def test_geodnet_delta_invalid() -> None:
    assert geodnet_baseline_confidence_delta(float("nan")) == 0
    assert geodnet_baseline_confidence_delta(-1) == 0


def test_combine_clamps() -> None:
    assert combine_motion_and_geodnet_baseline(95, 5_000) == 100
    assert combine_motion_and_geodnet_baseline(10, 500_000) == 0


def test_combine_without_baseline_is_motion_only() -> None:
    assert combine_motion_and_geodnet_baseline(85, None) == 85
