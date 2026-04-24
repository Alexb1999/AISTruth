# ADR 001: Public validation API sketch (v1)

## Status

Accepted sketch — implement against this shape; refine in ADR revisions.

## Context

External clients need a stable contract for track validation and explainability outputs described in the master scope.

## Decision

### `GET /v1/validate/{mmsi}` (future)

- **Path:** `mmsi` integer (9 digits typical).
- **Query:** `from` / `to` ISO-8601 UTC bounds (required for MVP to bound cost); optional `cursor` for pagination.
- **200 body (example keys):** `mmsi`, `window`, `confidence_score`, `flags[]`, `evidence` (inputs hash or snapshot id, `rules_version`, `nearest_node_id`, `baseline_m`, `time_align_method`).
- **Errors:** `400` invalid window; `404` no data for MMSI in window; `429` rate limit; `503` upstream AIS/GEODNET unavailable.

### Bulk (optional extension)

- `POST /v1/validate/batch` with JSON array of `{mmsi, from, to}` capped by configurable max items.

### Current implementation note

Shipped prototype: **`GET /v1/validate/{mmsi}`** with optional `from` / `to` query parameters (ISO-8601 UTC). It ingests **BarentsWatch** last-24h tracks, runs **implied-speed** heuristics in `aistruth_core.track_heuristics`, and attaches **PostGIS nearest-node** evidence when `DATABASE_URL` is configured. Optional **`geodnet_probe=true`** adds **`evidence.geodnet_ntrip_probe`** (live NTRIP bytes + coarse RTCM3 message histogram; GGA at latest AIS fix). **GEODNET / RTCM fusion is not yet applied**; `evidence.time_align_method` documents that.

Additional demos: `POST /v1/demo/time-align` and `GET /v1/nearest-node` exercise Gap 1 and Gap 2 fixtures.

## Consequences

- OpenAPI remains the source of truth at runtime (`/docs`).
- Version prefix `/v1` allows breaking changes under `/v2` without silent client breakage.
