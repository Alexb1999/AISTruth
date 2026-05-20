# aistruth-api

FastAPI application. Install from repository root (Python 3.11+; `uv` recommended):

```bash
uv venv .venv -p 3.11 && source .venv/bin/activate
uv pip install -e ./packages/core -e ./backend
```

Run Postgres + PostGIS (fixture nodes):

```bash
docker compose up -d
export DATABASE_URL=postgresql://aistruth:aistruth@localhost:5432/aistruth
```

Apply migrations for staging/production-like databases:

```bash
cd backend
DATABASE_URL=postgresql://aistruth:aistruth@localhost:5432/aistruth alembic upgrade head
```

`docker/init-db` remains a local bootstrap convenience; Alembic is the schema source of truth for `stg` and `prod`.

**GEODNET station catalog (map / nearest base):** After `alembic upgrade head`, the DB includes ~12 Norway **demo fixtures** along the coast. For discovery demos that must match [rtk.geodnet.com](https://rtk.geodnet.com/) density, sync the live catalog:

```bash
export GEODNET_RTK_APP_ID="..."
export GEODNET_RTK_APP_KEY="..."
# optional: export GEODNET_RTK_STATION_REGION=NOR
curl -X POST http://127.0.0.1:8000/v1/geodnet/sync-stations -H "X-AIS-Key: $AISTRUTH_API_KEYS"
```

Or set `GEODNET_SYNC_STATIONS_AT_STARTUP=true` on API boot. See [docs/integrations/geodnet-rtk.md](../docs/integrations/geodnet-rtk.md). Validate responses include `evidence.geodnet_catalog` and K-nearest `geodnet_map_nodes` for the console map.

**Pilot tenants (Phase 1):** After migrations through `20260520_0005`:

```bash
cd backend
uv run python scripts/create_pilot_tenant.py --name "Acme Pilot" --slug acme-pilot --ais-source barentswatch
```

Prints a one-time `X-AIS-Key`. Use `GET /v1/me` to confirm tenant context; `GET /v1/admin/usage` with `X-Admin-Key` for month-to-date units. Set `AISTRUTH_AIS_SOURCE=file` and `FILE_REPLAY_PATH=tests/fixtures/sample_track.jsonl` for replay demos. See [docs/adr/004-tenant-and-usage.md](../docs/adr/004-tenant-and-usage.md).

Start the API:

```bash
cd backend && uvicorn main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for OpenAPI.

Without `DATABASE_URL`, `/v1/nearest-node` returns 503; `/health` and `/v1/demo/time-align` still work.

**Norwegian open AIS (BarentsWatch):** set `BARENTSWATCH_CLIENT_ID` and `BARENTSWATCH_CLIENT_SECRET`, then use `GET /v1/ais/norway/track/{mmsi}` or `GET /v1/ais/norway/latest?mmsi=…`. See [docs/integrations/barentswatch-ais.md](../../docs/integrations/barentswatch-ais.md).

## API key auth

Set `AISTRUTH_API_KEYS` to a comma-separated allow-list before exposing `/v1/*` routes outside local development:

```bash
export AISTRUTH_API_KEYS="dev-key-1,staging-key-2"
curl -H "X-AIS-Key: dev-key-1" http://127.0.0.1:8000/v1/validate/257000000
```

If `AISTRUTH_API_KEYS` is empty, auth is disabled for local development. `/health` is always public.
