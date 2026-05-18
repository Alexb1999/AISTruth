from __future__ import annotations

from alembic import op

revision = "20260425_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS geodnet_nodes (
            id text PRIMARY KEY,
            name text NOT NULL,
            active boolean NOT NULL DEFAULT true,
            geom geography(POINT, 4326) NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS geodnet_nodes_gix
        ON geodnet_nodes USING gist (geom)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS validation_runs (
            id uuid PRIMARY KEY,
            mmsi integer NOT NULL,
            requested_at timestamptz NOT NULL DEFAULT now(),
            window_from timestamptz NOT NULL,
            window_to timestamptz NOT NULL,
            confidence_score integer NOT NULL,
            flags text[] NOT NULL DEFAULT '{}',
            evidence jsonb NOT NULL,
            rules_version text NOT NULL,
            nearest_node_id text NULL REFERENCES geodnet_nodes(id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS validation_runs_mmsi_requested_at_idx
        ON validation_runs (mmsi, requested_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ais_track_cache (
            mmsi integer NOT NULL,
            point_t timestamptz NOT NULL,
            lat double precision NOT NULL,
            lon double precision NOT NULL,
            source text NOT NULL,
            PRIMARY KEY (mmsi, point_t, source)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ais_track_cache")
    op.execute("DROP TABLE IF EXISTS validation_runs")
    op.execute("DROP INDEX IF EXISTS geodnet_nodes_gix")
    op.execute("DROP TABLE IF EXISTS geodnet_nodes")
