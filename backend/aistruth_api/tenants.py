"""Tenant records and API key resolution."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


@dataclass(frozen=True)
class TenantRecord:
    id: UUID
    name: str
    slug: str
    ais_source: str
    spire_api_key: str | None
    file_replay_path: str | None
    pilot_ends_at: datetime | None


@dataclass(frozen=True)
class ApiKeyAuth:
    tenant: TenantRecord
    api_key_id: UUID


def _row_to_tenant(row: asyncpg.Record) -> TenantRecord:
    return TenantRecord(
        id=row["id"],
        name=str(row["name"]),
        slug=str(row["slug"]),
        ais_source=str(row["ais_source"]),
        spire_api_key=row["spire_api_key"],
        file_replay_path=row["file_replay_path"],
        pilot_ends_at=row["pilot_ends_at"],
    )


async def lookup_auth_by_raw_key(conn: asyncpg.Connection, raw_key: str) -> ApiKeyAuth | None:
    key_hash = hash_api_key(raw_key)
    row = await conn.fetchrow(
        """
        SELECT
            k.id AS api_key_id,
            t.id,
            t.name,
            t.slug,
            t.ais_source,
            t.spire_api_key,
            t.file_replay_path,
            t.pilot_ends_at
        FROM api_keys k
        JOIN tenants t ON t.id = k.tenant_id
        WHERE k.key_hash = $1
          AND k.revoked_at IS NULL
        """,
        key_hash,
    )
    if row is None:
        return None
    return ApiKeyAuth(tenant=_row_to_tenant(row), api_key_id=row["api_key_id"])


async def create_tenant_with_key(
    conn: asyncpg.Connection,
    *,
    name: str,
    slug: str,
    ais_source: str = "barentswatch",
    spire_api_key: str | None = None,
    file_replay_path: str | None = None,
    pilot_ends_at: datetime | None = None,
    key_label: str = "default",
) -> tuple[TenantRecord, str]:
    """Insert tenant + API key; returns tenant row and one-time raw key."""
    raw_key = generate_api_key()
    tenant_row = await conn.fetchrow(
        """
        INSERT INTO tenants (
            name, slug, ais_source, spire_api_key, file_replay_path, pilot_ends_at
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, name, slug, ais_source, spire_api_key, file_replay_path, pilot_ends_at
        """,
        name,
        slug,
        ais_source,
        spire_api_key,
        file_replay_path,
        pilot_ends_at,
    )
    if tenant_row is None:
        raise RuntimeError("tenant insert failed")
    await conn.execute(
        """
        INSERT INTO api_keys (tenant_id, key_hash, label)
        VALUES ($1, $2, $3)
        """,
        tenant_row["id"],
        hash_api_key(raw_key),
        key_label,
    )
    return _row_to_tenant(tenant_row), raw_key


async def fetch_tenant_by_id(conn: asyncpg.Connection, tenant_id: UUID) -> TenantRecord | None:
    row = await conn.fetchrow(
        """
        SELECT id, name, slug, ais_source, spire_api_key, file_replay_path, pilot_ends_at
        FROM tenants
        WHERE id = $1
        """,
        tenant_id,
    )
    if row is None:
        return None
    return _row_to_tenant(row)


def tenant_public_dict(tenant: TenantRecord) -> dict[str, Any]:
    return {
        "slug": tenant.slug,
        "name": tenant.name,
        "ais_source": tenant.ais_source,
        "pilot_ends_at": tenant.pilot_ends_at.isoformat() if tenant.pilot_ends_at else None,
    }
