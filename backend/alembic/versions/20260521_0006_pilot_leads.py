"""Pilot lead capture (Phase 2 GTM).

Revision ID: 20260521_0006
Revises: 20260520_0005
Create Date: 2026-05-21
"""

from __future__ import annotations

from alembic import op

revision = "20260521_0006"
down_revision = "20260520_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pilot_leads (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            organization text NOT NULL,
            email text NOT NULL,
            region text NOT NULL,
            fleet_size text NULL,
            ais_feed text NULL,
            message text NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS pilot_leads_created_at_idx
            ON pilot_leads (created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pilot_leads")
