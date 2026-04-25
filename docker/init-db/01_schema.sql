CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE geodnet_nodes (
    id text PRIMARY KEY,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    geom geography (POINT, 4326) NOT NULL
);

CREATE INDEX geodnet_nodes_gix ON geodnet_nodes USING gist (geom);

-- Demo fixtures (Nova Scotia area); replace with live GEODNET sync later.
INSERT INTO geodnet_nodes (id, name, geom)
VALUES
    ('demo-halifax', 'Demo node Halifax', ST_GeogFromText('SRID=4326;POINT(-63.5752 44.6488)')),
    ('demo-lunenburg', 'Demo node Lunenburg', ST_GeogFromText('SRID=4326;POINT(-64.3198 44.3770)'));

-- Dev convenience only. Alembic is the source of truth for staging/production schemas.
CREATE TABLE validation_runs (
    id uuid PRIMARY KEY,
    mmsi integer NOT NULL,
    requested_at timestamptz NOT NULL DEFAULT now(),
    window_from timestamptz NOT NULL,
    window_to timestamptz NOT NULL,
    confidence_score integer NOT NULL,
    flags text[] NOT NULL DEFAULT '{}',
    evidence jsonb NOT NULL,
    rules_version text NOT NULL,
    nearest_node_id text NULL REFERENCES geodnet_nodes (id)
);

CREATE INDEX validation_runs_mmsi_requested_at_idx
ON validation_runs (mmsi, requested_at DESC);

CREATE TABLE ais_track_cache (
    mmsi integer NOT NULL,
    point_t timestamptz NOT NULL,
    lat double precision NOT NULL,
    lon double precision NOT NULL,
    source text NOT NULL,
    PRIMARY KEY (mmsi, point_t, source)
);
