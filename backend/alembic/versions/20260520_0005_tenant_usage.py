"""Tenant identity, API keys, usage metering (Phase 1 pilot infrastructure).

Revision ID: 20260520_0005
Revises: 20260519_0004
Create Date: 2026-05-20
"""

from __future__ import annotations

from alembic import op

revision = "20260520_0005"
down_revision = "20260519_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            slug text NOT NULL UNIQUE,
            ais_source text NOT NULL DEFAULT 'barentswatch',
            spire_api_key text NULL,
            file_replay_path text NULL,
            pilot_ends_at timestamptz NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            key_hash text NOT NULL UNIQUE,
            label text NOT NULL DEFAULT 'default',
            revoked_at timestamptz NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS api_keys_tenant_id_idx ON api_keys (tenant_id)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NULL REFERENCES tenants(id) ON DELETE SET NULL,
            api_key_id uuid NULL REFERENCES api_keys(id) ON DELETE SET NULL,
            route text NOT NULL,
            mmsi integer NULL,
            units integer NOT NULL DEFAULT 1,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS usage_events_tenant_created_idx
        ON usage_events (tenant_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlists (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name text NOT NULL,
            mmsi_list integer[] NOT NULL DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, name)
        )
        """
    )
    op.execute(
        """
        ALTER TABLE validation_runs
        ADD COLUMN IF NOT EXISTS tenant_id uuid NULL REFERENCES tenants(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS validation_runs_tenant_mmsi_idx
        ON validation_runs (tenant_id, mmsi, requested_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS validation_runs_tenant_mmsi_idx")
    op.execute("ALTER TABLE validation_runs DROP COLUMN IF EXISTS tenant_id")
    op.execute("DROP TABLE IF EXISTS watchlists")
    op.execute("DROP INDEX IF EXISTS usage_events_tenant_created_idx")
    op.execute("DROP TABLE IF EXISTS usage_events")
    op.execute("DROP INDEX IF EXISTS api_keys_tenant_id_idx")
    op.execute("DROP TABLE IF EXISTS api_keys")
    op.execute("DROP TABLE IF EXISTS tenants")
