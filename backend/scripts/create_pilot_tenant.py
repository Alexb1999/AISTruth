#!/usr/bin/env python3
"""Create a pilot tenant and print a one-time API key."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import UTC, datetime

import asyncpg

from aistruth_api.tenants import create_tenant_with_key


def _parse_pilot_end(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


async def _run(args: argparse.Namespace) -> int:
    database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required", file=sys.stderr)
        return 1

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    assert pool is not None
    try:
        async with pool.acquire() as conn, conn.transaction():
            tenant, raw_key = await create_tenant_with_key(
                conn,
                name=args.name,
                slug=args.slug,
                ais_source=args.ais_source,
                spire_api_key=args.spire_api_key,
                file_replay_path=args.file_replay_path,
                pilot_ends_at=_parse_pilot_end(args.pilot_ends_at),
                key_label=args.key_label,
            )
    finally:
        await pool.close()

    print(f"tenant_slug={tenant.slug}")
    print(f"tenant_id={tenant.id}")
    print(f"ais_source={tenant.ais_source}")
    print(f"api_key={raw_key}")
    print("Store the API key now — it cannot be retrieved again.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a pilot tenant + API key.")
    parser.add_argument("--name", required=True, help="Display name, e.g. Acme Charter Pilot")
    parser.add_argument("--slug", required=True, help="Unique slug, e.g. acme-charter")
    parser.add_argument(
        "--ais-source",
        default="barentswatch",
        choices=("barentswatch", "spire", "file"),
    )
    parser.add_argument("--spire-api-key", default=None)
    parser.add_argument("--file-replay-path", default=None)
    parser.add_argument("--pilot-ends-at", default=None, help="ISO8601 datetime")
    parser.add_argument("--key-label", default="pilot")
    parser.add_argument("--database-url", default=None)
    raise SystemExit(asyncio.run(_run(parser.parse_args())))


if __name__ == "__main__":
    main()
