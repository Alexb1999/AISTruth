# ⚓ AISTruth

> **The Source of Truth for Maritime Positioning.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Stack: Next.js + FastAPI](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI-black)](https://nextjs.org/)
[![Network: GEODNET](https://img.shields.io/badge/Network-GEODNET-orange)](https://geodnet.com/)

## 🌊 The Mission

Standard AIS data is "noisy" and vulnerable. **AISTruth** provides a high-fidelity verification layer by fusing AIS tracks, coastal context, GEODNET correction telemetry, and integrity heuristics. The long-term goal is centimeter-class RTK validation where rover observations and geometry support it; the current MVP focuses on auditable integrity evidence without overclaiming a solved rover position.

## 🚀 Key Capabilities

- **RTK Evidence Contract:** Validate GEODNET correction stream freshness and expose an `rtk_v1` evidence shape ready for a future rover-observation solver.
- **Spoofing Guard:** Detect suspicious track behavior with impossible-jump, freeze, and identity-swap findings.
- **Integrity Scoring:** A proprietary "Trust Score" for vessels in coastal validation zones wherever GEODNET coverage supports fusion.
- **Cloud-First:** Fuse AIS with the public GEODNET network—no owned miner or coastal "super node" required to ship the MVP.

## 📄 Documentation

- [ADR 001 — API contract sketch](docs/adr/001-api-contract-sketch.md): early `/v1/validate` shape and error model.
- [BarentsWatch AIS (Phase 1 dev feed)](docs/integrations/barentswatch-ais.md): Norwegian open AIS — credentials and API routes.
- [GEODNET RTK / NTRIP](docs/integrations/geodnet-rtk.md): caster notes, trial vs paid, and the `scripts/ntrip_smoke.py` smoke test.

## 🏗 Project Structure

- `frontend/`: Next.js 14 + Tailwind — **marketing** at `/` and **dev console** at `/console` (`npm install && npm run dev` from this folder, or `npm run dev` from repo root).
- `backend/`: Runnable FastAPI app (`uvicorn main:app` from this directory); OpenAPI at `/docs`.
- `packages/core`: Truth-engine library (`aistruth_core`: time sync, RTCM/MSM helpers, spoofing findings, AIS adapters).
- `docker/`: PostGIS fixture schema for nearest-node demos and validation persistence.
- `hardware` (optional/future): Notes for any proprietary ground station; not required for the core SaaS path.

## 💻 Local development

**Requirements:** Python **3.11+**, **Node 18+**, and (for nearest-node + persistence) **Docker** or any **PostgreSQL + PostGIS** with `DATABASE_URL`.

### 1. Database (optional but recommended)

From the **repo root**:

```bash
docker compose up -d db
export DATABASE_URL="postgresql://aistruth:aistruth@localhost:5432/aistruth"
```

The first boot runs `docker/init-db` (demo `geodnet_nodes` + app tables). Then apply Alembic from the API package:

```bash
cd backend
uv sync --all-extras
uv run alembic upgrade head
```

### 2. API

Copy `backend/.env.example` → `backend/.env` and set **BarentsWatch** credentials (required for `/v1/validate`). Keep `DATABASE_URL` if you use Postgres.

From **`backend`**:

```bash
uv sync --all-extras
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). `/health` stays public; `/v1/*` uses `X-AIS-Key` when `AISTRUTH_API_KEYS` is non-empty.

Without `DATABASE_URL`, validate still runs, but **nearest-node** and **DB persistence** are skipped (`503` on `/v1/nearest-node`).

### 3. Web app

From **`frontend`**:

```bash
npm install
cp .env.example .env.local   # optional; defaults already match local API
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) for the **landing page** and [http://localhost:3000/console](http://localhost:3000/console) for **validation**. The UI calls `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`). Ensure the API’s `AISTRUTH_CORS_ORIGINS` includes `http://localhost:3000` (default in `.env.example`).

### Older one-liner (still valid)

```bash
uv venv .venv -p 3.11 && source .venv/bin/activate
uv pip install -e "./packages/core[dev]" -e "./backend[dev]"
pytest packages/core/tests backend/tests -q
```

**GEODNET NTRIP telemetry (dev):** with `GEODNET_NTRIP_USER` / `GEODNET_NTRIP_PASSWORD` on the API, call **`GET /v1/debug/geodnet-ntrip?seconds=5`** (requires `AISTRUTH_ENABLE_GEODNET_DEBUG=true`), or **`GET /v1/validate/{mmsi}?geodnet_probe=true`**. See [docs/integrations/geodnet-rtk.md](docs/integrations/geodnet-rtk.md). **Smoke script:** `python scripts/ntrip_smoke.py --seconds 20` with the same NTRIP env vars.

## 🛠 Tech Stack

- **Languages:** Python (Data Science/API), TypeScript (Frontend).
- **Currently shipped:** FastAPI, Next.js 14, Tailwind, Leaflet, PostGIS, Alembic, async BarentsWatch HTTP ingest, RTCM/MSM telemetry helpers, spoofing findings, file replay, and Spire-shaped BYOK adapter.
- **Planned:** True RTK solver integration once rover GNSS observations are available.

## MVP Boundary

The MVP proves ingest, time alignment, nearest-node context, correction-stream telemetry, scoring evidence, persistence, and dashboard workflows. It does **not** yet prove centimeter-class vessel position correction because AIS alone is not a rover GNSS observation stream.

---

*Built by Alex Boutilier | Maritime Data Science & DePIN Infrastructure*