"""Add ingest metadata columns to geodnet_nodes for API sync.

Revision ID: 20260517_0003
Revises: 20260517_0002
"""

from __future__ import annotations

from alembic import op

revision = "20260517_0003"
down_revision = "20260517_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE geodnet_nodes
        ADD COLUMN IF NOT EXISTS ingest_source text NOT NULL DEFAULT 'fixture',
        ADD COLUMN IF NOT EXISTS station_status text NULL,
        ADD COLUMN IF NOT EXISTS synced_at timestamptz NULL
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN geodnet_nodes.ingest_source IS
        'fixture: seeded demo; geodnet_rtk_api: from /api/v3/station/list'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE geodnet_nodes DROP COLUMN IF EXISTS synced_at")
    op.execute("ALTER TABLE geodnet_nodes DROP COLUMN IF EXISTS station_status")
    op.execute("ALTER TABLE geodnet_nodes DROP COLUMN IF EXISTS ingest_source")
