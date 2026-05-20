"""Usage event logging and admin summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg


async def log_usage_event(
    pool: asyncpg.Pool,
    *,
    route: str,
    tenant_id: UUID | None,
    api_key_id: UUID | None,
    mmsi: int | None,
    units: int = 1,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO usage_events (id, tenant_id, api_key_id, route, mmsi, units)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            uuid4(),
            tenant_id,
            api_key_id,
            route,
            mmsi,
            units,
        )


async def usage_summary_current_month(pool: asyncpg.Pool) -> list[dict[str, Any]]:
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                t.slug,
                t.name,
                COUNT(*) AS event_count,
                COALESCE(SUM(u.units), 0) AS units_total,
                COUNT(*) FILTER (WHERE u.route LIKE '%validate%') AS validate_calls
            FROM usage_events u
            LEFT JOIN tenants t ON t.id = u.tenant_id
            WHERE u.created_at >= $1
            GROUP BY t.slug, t.name
            ORDER BY units_total DESC, event_count DESC
            """,
            month_start,
        )
    return [
        {
            "tenant_slug": row["slug"],
            "tenant_name": row["name"],
            "event_count": int(row["event_count"]),
            "units_total": int(row["units_total"]),
            "validate_calls": int(row["validate_calls"]),
        }
        for row in rows
    ]
