"""GEODNET station catalog queries for validate evidence and map overlays."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg

K_NEAREST_MAP_NODES = 10
SYNCED_CATALOG_MIN_NODES = 20


def catalog_mode_from_counts(synced_count: int) -> str:
    """Classify catalog for UI banners: fixture, hybrid, or synced."""
    if synced_count >= SYNCED_CATALOG_MIN_NODES:
        return "synced"
    if synced_count > 0:
        return "hybrid"
    return "fixture"


async def fetch_catalog_summary(conn: asyncpg.Connection) -> dict[str, Any]:
    """Summarize active nodes in ``geodnet_nodes`` for honesty banners and evidence."""
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE active) AS active_count,
            COUNT(*) FILTER (WHERE active AND ingest_source = 'geodnet_rtk_api') AS synced_count,
            COUNT(*) FILTER (WHERE active AND ingest_source = 'fixture') AS fixture_count,
            MAX(synced_at) FILTER (WHERE ingest_source = 'geodnet_rtk_api') AS last_synced_at
        FROM geodnet_nodes
        """
    )
    active_count = int(row["active_count"] or 0) if row else 0
    synced_count = int(row["synced_count"] or 0) if row else 0
    fixture_count = int(row["fixture_count"] or 0) if row else 0
    last_synced_at = row["last_synced_at"] if row else None

    mode = catalog_mode_from_counts(synced_count)

    return {
        "mode": mode,
        "active_node_count": active_count,
        "synced_node_count": synced_count,
        "fixture_node_count": fixture_count,
        "last_synced_at": last_synced_at.isoformat() if isinstance(last_synced_at, datetime) else None,
        "demo_warning": active_count < SYNCED_CATALOG_MIN_NODES,
    }


async def fetch_k_nearest_nodes(
    conn: asyncpg.Connection,
    *,
    lon: float,
    lat: float,
    limit: int = K_NEAREST_MAP_NODES,
) -> list[dict[str, Any]]:
    """Return nearest active stations with distance in meters, closest first."""
    rows = await conn.fetch(
        """
        SELECT id,
               name,
               ST_Y(geom::geometry) AS lat,
               ST_X(geom::geometry) AS lon,
               ST_Distance(
                   geom,
                   ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
               ) AS dist_m
        FROM geodnet_nodes
        WHERE active
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
        LIMIT $3
        """,
        lon,
        lat,
        limit,
    )
    out: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        out.append(
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "distance_m": float(row["dist_m"]),
                "is_nearest": i == 0,
            }
        )
    return out


def nearest_from_k_list(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build ``nearest_node`` evidence object from the first K-nearest row."""
    if not nodes:
        return None
    n = nodes[0]
    return {
        "id": n["id"],
        "name": n["name"],
        "lat": n["lat"],
        "lon": n["lon"],
        "distance_m": n["distance_m"],
    }


def map_nodes_for_evidence(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip distance fields for ``geodnet_map_nodes`` (optional fields kept for UI)."""
    return [
        {
            "id": n["id"],
            "name": n["name"],
            "lat": n["lat"],
            "lon": n["lon"],
            "distance_m": n.get("distance_m"),
            "is_nearest": n.get("is_nearest", False),
        }
        for n in nodes
    ]
