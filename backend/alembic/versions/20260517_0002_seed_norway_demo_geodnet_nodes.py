"""Seed Norwegian demo geodnet_nodes for BarentsWatch validation.

Revision ID: 20260517_0002
Revises: 20260425_0001
Create Date: 2026-05-17

Nova Scotia demo nodes remain in docker/init-db only unless also inserted
elsewhere; this migration only adds NO coastal fixtures for Alembic-managed DBs.
Downgrade clears Norway demo ids and nulls validation_runs references.
"""

from __future__ import annotations

from alembic import op

revision = "20260517_0002"
down_revision = "20260425_0001"
branch_labels = None
depends_on = None

_DEMO_NO_IDS = (
    "demo-no-oslo",
    "demo-no-bergen",
    "demo-no-stavanger",
    "demo-no-kristiansand",
    "demo-no-bodo",
    "demo-no-tromso",
)


def upgrade() -> None:
    # POINT WKT order is (lon lat). Fixtures are approximate port anchors, not live miners.
    op.execute(
        """
        INSERT INTO geodnet_nodes (id, name, geom) VALUES
        ('demo-no-oslo', 'Demo node Oslo (NO)',
         ST_GeogFromText('SRID=4326;POINT(10.7522 59.9139)')),
        ('demo-no-bergen', 'Demo node Bergen (NO)',
         ST_GeogFromText('SRID=4326;POINT(5.3221 60.3913)')),
        ('demo-no-stavanger', 'Demo node Stavanger (NO)',
         ST_GeogFromText('SRID=4326;POINT(5.7331 58.9700)')),
        ('demo-no-kristiansand', 'Demo node Kristiansand (NO)',
         ST_GeogFromText('SRID=4326;POINT(7.9956 58.1467)')),
        ('demo-no-bodo', 'Demo node Bodø (NO)',
         ST_GeogFromText('SRID=4326;POINT(14.4049 67.2804)')),
        ('demo-no-tromso', 'Demo node Tromsø (NO)',
         ST_GeogFromText('SRID=4326;POINT(18.9553 69.6492)'))
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    ids = ", ".join(f"'{i}'" for i in _DEMO_NO_IDS)
    op.execute(
        f"""
        UPDATE validation_runs
        SET nearest_node_id = NULL
        WHERE nearest_node_id IN ({ids})
        """
    )
    op.execute(
        f"""
        DELETE FROM geodnet_nodes WHERE id IN ({ids})
        """
    )
