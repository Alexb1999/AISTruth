"""Tests for GEODNET catalog helpers (Phase 0)."""

from __future__ import annotations

from aistruth_api.integrations.geodnet_catalog import (
    SYNCED_CATALOG_MIN_NODES,
    catalog_mode_from_counts,
    map_nodes_for_evidence,
    nearest_from_k_list,
)


def test_catalog_mode_fixture_only() -> None:
    assert catalog_mode_from_counts(0) == "fixture"


def test_catalog_mode_synced() -> None:
    assert catalog_mode_from_counts(SYNCED_CATALOG_MIN_NODES) == "synced"
    assert catalog_mode_from_counts(500) == "synced"


def test_catalog_mode_hybrid() -> None:
    assert catalog_mode_from_counts(3) == "hybrid"


def test_nearest_from_k_list_empty() -> None:
    assert nearest_from_k_list([]) is None


def test_map_nodes_preserves_distance() -> None:
    nodes = [
        {
            "id": "a",
            "name": "A",
            "lat": 62.0,
            "lon": 7.0,
            "distance_m": 1200.0,
            "is_nearest": True,
        }
    ]
    out = map_nodes_for_evidence(nodes)
    assert out[0]["distance_m"] == 1200.0
    assert out[0]["is_nearest"] is True
