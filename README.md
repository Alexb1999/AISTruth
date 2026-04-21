# ⚓ AISTruth

> **The Source of Truth for Maritime Positioning.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Stack: Next.js + FastAPI](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI-black)](https://nextjs.org/)
[![Network: GEODNET](https://img.shields.io/badge/Network-GEODNET-orange)](https://geodnet.com/)

## 🌊 The Mission

Standard AIS data is "noisy" and vulnerable. **AISTruth** provides a high-fidelity verification layer by fusing global AIS streams with local GEODNET RTK (Real-Time Kinematic) corrections. We turn 5-meter uncertainty into 2-centimeter certainty.

## 🚀 Key Capabilities

- **RTK-Corrected AIS:** Apply centimeter-level ground truth to coastal vessel traffic.
- **Spoofing Guard:** Detect GNSS manipulation by cross-referencing vessel reports with local ionospheric noise profiles.
- **Integrity Scoring:** A proprietary "Trust Score" for vessels in coastal validation zones wherever GEODNET coverage supports fusion.
- **Cloud-First:** Fuse AIS with the public GEODNET network—no owned miner or coastal "super node" required to ship the MVP.

## 📄 Documentation

- [Master scope & architecture](docs/AISTruth_Master_Scope.md): cloud-first SaaS blueprint, GEODNET fusion gaps, branching (`dev` / `stg` / `prod`), integration appendix (CRS, legal, API sketch link), roadmap, and monetization.
- [ADR 001 — API contract sketch](docs/adr/001-api-contract-sketch.md): early `/v1/validate` shape and error model.

## 🏗 Project Structure

- `apps/web`: Next.js dashboard (placeholder README until Phase 1 UI scaffold).
- `apps/api`: Runnable FastAPI app (`uvicorn main:app` from this directory); OpenAPI at `/docs`.
- `packages/core`: Truth-engine library (`aistruth_core`: time sync, AIS `Protocol` stubs).
- `docker/`: PostGIS fixture schema for nearest-node demos.
- `hardware` (optional/future): Notes for any proprietary ground station; not required for the core SaaS path.

## 💻 Local development

Requires **Python 3.11+** and optionally **Docker** for PostGIS-backed routes. Using [uv](https://docs.astral.sh/uv/) avoids PEP 668 issues on managed Python installs:

```bash
uv venv .venv -p 3.11 && source .venv/bin/activate
uv pip install -e "./packages/core[dev]" -e "./apps/api"
pytest packages/core/tests -q
docker compose up -d
export DATABASE_URL=postgresql://aistruth:aistruth@localhost:5432/aistruth
cd apps/api && uvicorn main:app --reload
```

Without `DATABASE_URL`, `/health` and `POST /v1/demo/time-align` still run; `GET /v1/nearest-node` returns 503 until Postgres is up.

## 🛠 Tech Stack

- **Languages:** Python (Data Science/API), TypeScript (Frontend).
- **Frameworks:** FastAPI, Next.js 14, Tailwind CSS.
- **Geospatial:** PostGIS, Leaflet/Mapbox, `pyais`, `gnss-lib-py`.

---

*Built by Alex Boutilier | Maritime Data Science & DePIN Infrastructure*