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

Start the API:

```bash
cd apps/api && uvicorn main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for OpenAPI.

Without `DATABASE_URL`, `/v1/nearest-node` returns 503; `/health` and `/v1/demo/time-align` still work.
