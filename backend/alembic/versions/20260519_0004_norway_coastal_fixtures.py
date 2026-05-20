"""Add central-Norway coastal demo nodes; mark all demo rows as fixture ingest.

Revision ID: 20260519_0004
Revises: 20260517_0003
Create Date: 2026-05-19

Fills the Bergen–Bodø gap so local demos without GEODNET API sync show plausible
nearest bases along the Norwegian coast.
"""

from __future__ import annotations

from alembic import op

revision = "20260519_0004"
down_revision = "20260517_0003"
branch_labels = None
depends_on = None

_ALL_DEMO_NO_IDS = (
    "demo-no-oslo",
    "demo-no-bergen",
    "demo-no-stavanger",
    "demo-no-kristiansand",
    "demo-no-bodo",
    "demo-no-tromso",
    "demo-no-alesund",
    "demo-no-molde",
    "demo-no-kristiansund",
    "demo-no-trondheim",
    "demo-no-andalsnes",
    "demo-no-narvik",
)

_NEW_IDS = (
    "demo-no-alesund",
    "demo-no-molde",
    "demo-no-kristiansund",
    "demo-no-trondheim",
    "demo-no-andalsnes",
    "demo-no-narvik",
)


def upgrade() -> None:
    ids = ", ".join(f"'{i}'" for i in _ALL_DEMO_NO_IDS)
    op.execute(
        f"""
        UPDATE geodnet_nodes
        SET ingest_source = 'fixture'
        WHERE id IN ({ids})
           OR id LIKE 'demo-no-%'
        """
    )
    op.execute(
        """
        INSERT INTO geodnet_nodes (id, name, active, geom, ingest_source) VALUES
        ('demo-no-alesund', 'Demo node Ålesund (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(6.1549 62.4722)'), 'fixture'),
        ('demo-no-molde', 'Demo node Molde (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(7.1617 62.7372)'), 'fixture'),
        ('demo-no-kristiansund', 'Demo node Kristiansund (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(7.7279 63.1105)'), 'fixture'),
        ('demo-no-trondheim', 'Demo node Trondheim (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(10.3951 63.4305)'), 'fixture'),
        ('demo-no-andalsnes', 'Demo node Åndalsnes (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(7.6882 62.5675)'), 'fixture'),
        ('demo-no-narvik', 'Demo node Narvik (NO)', true,
         ST_GeogFromText('SRID=4326;POINT(17.4272 68.4385)'), 'fixture')
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            active = EXCLUDED.active,
            geom = EXCLUDED.geom,
            ingest_source = 'fixture'
        """
    )


def downgrade() -> None:
    new_ids = ", ".join(f"'{i}'" for i in _NEW_IDS)
    op.execute(
        f"""
        UPDATE validation_runs
        SET nearest_node_id = NULL
        WHERE nearest_node_id IN ({new_ids})
        """
    )
    op.execute(f"DELETE FROM geodnet_nodes WHERE id IN ({new_ids})")
