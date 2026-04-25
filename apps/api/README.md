# aistruth-api

FastAPI application. Install from repository root (Python 3.11+; `uv` recommended):

```bash
uv venv .venv -p 3.11 && source .venv/bin/activate
uv pip install -e ./packages/core -e ./apps/api
```

Run Postgres + PostGIS (fixture nodes):

```bash
docker compose up -d
export DATABASE_URL=postgresql://aistruth:aistruth@localhost:5432/aistruth
```

Apply migrations for staging/production-like databases:

```bash
cd apps/api
DATABASE_URL=postgresql://aistruth:aistruth@localhost:5432/aistruth alembic upgrade head
```

`docker/init-db` remains a local bootstrap convenience; Alembic is the schema source of truth for `stg` and `prod`.

Start the API:

```bash
cd apps/api && uvicorn main:app --reload
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
