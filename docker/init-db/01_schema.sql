CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE geodnet_nodes (
    id text PRIMARY KEY,
    name text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    geom geography (POINT, 4326) NOT NULL,
    ingest_source text NOT NULL DEFAULT 'fixture',
    station_status text NULL,
    synced_at timestamptz NULL
);

CREATE INDEX geodnet_nodes_gix ON geodnet_nodes USING gist (geom);

-- Demo fixtures (not live GEODNET): NS for map demos, Norway for BarentsWatch dev tracks.
INSERT INTO geodnet_nodes (id, name, geom)
VALUES
    ('demo-halifax', 'Demo node Halifax', ST_GeogFromText('SRID=4326;POINT(-63.5752 44.6488)')),
    ('demo-lunenburg', 'Demo node Lunenburg', ST_GeogFromText('SRID=4326;POINT(-64.3198 44.3770)')),
    ('demo-no-oslo', 'Demo node Oslo (NO)', ST_GeogFromText('SRID=4326;POINT(10.7522 59.9139)')),
    ('demo-no-bergen', 'Demo node Bergen (NO)', ST_GeogFromText('SRID=4326;POINT(5.3221 60.3913)')),
    ('demo-no-stavanger', 'Demo node Stavanger (NO)', ST_GeogFromText('SRID=4326;POINT(5.7331 58.9700)')),
    ('demo-no-kristiansand', 'Demo node Kristiansand (NO)', ST_GeogFromText('SRID=4326;POINT(7.9956 58.1467)')),
    ('demo-no-bodo', 'Demo node Bodø (NO)', ST_GeogFromText('SRID=4326;POINT(14.4049 67.2804)')),
    ('demo-no-tromso', 'Demo node Tromsø (NO)', ST_GeogFromText('SRID=4326;POINT(18.9553 69.6492)')),
    ('demo-no-alesund', 'Demo node Ålesund (NO)', ST_GeogFromText('SRID=4326;POINT(6.1549 62.4722)')),
    ('demo-no-molde', 'Demo node Molde (NO)', ST_GeogFromText('SRID=4326;POINT(7.1617 62.7372)')),
    ('demo-no-kristiansund', 'Demo node Kristiansund (NO)', ST_GeogFromText('SRID=4326;POINT(7.7279 63.1105)')),
    ('demo-no-trondheim', 'Demo node Trondheim (NO)', ST_GeogFromText('SRID=4326;POINT(10.3951 63.4305)')),
    ('demo-no-andalsnes', 'Demo node Åndalsnes (NO)', ST_GeogFromText('SRID=4326;POINT(7.6882 62.5675)')),
    ('demo-no-narvik', 'Demo node Narvik (NO)', ST_GeogFromText('SRID=4326;POINT(17.4272 68.4385)'));

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
