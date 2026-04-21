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
