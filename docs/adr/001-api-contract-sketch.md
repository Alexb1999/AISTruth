# ADR 001: Public validation API contract (v1)

## Status

Accepted.

## Context

External clients need a stable contract for track validation and explainability outputs described in the master scope.

## Decision

### `GET /v1/validate/{mmsi}`

- **Path:** `mmsi` integer (9 digits typical).
- **Query:** optional `from` / `to` ISO-8601 UTC bounds, optional `geodnet_probe=true`, optional `fusion=true`.
- **200 body:** `mmsi`, `window`, `confidence_score`, `flags[]`, `evidence`.
- **Evidence:** `rules_version`, `nearest_node_id`, `baseline_m`, `max_implied_speed_knots`, `time_align_method`, `spoofing_findings[]`, optional `geodnet_ntrip_probe`, optional `fusion_result`.
- **Errors:** `400` invalid window; `404` no data for MMSI in window; `429` rate limit; `503` upstream AIS/GEODNET unavailable.

### `POST /v1/validate/bulk`

- **Body:** `{ "mmsi": [257000000], "from": "...", "to": "...", "fusion": false }`.
- **200 body:** `{ "results": [{ "mmsi": 257000000, "result": {...}, "error": null, "status_code": null }] }`.
- Per-MMSI failures are returned in the item-level `error` / `status_code` fields rather than failing the whole bulk request.

### Supporting routes

- `GET /v1/validate/{mmsi}/history` returns persisted validation runs when `DATABASE_URL` is configured.
- `POST /v1/demo/time-align` exercises the slerp time-alignment path.
- `GET /v1/nearest-node` exercises PostGIS nearest-node lookup.
- `GET /v1/debug/geodnet-ntrip` is dev-only and gated by `AISTRUTH_ENABLE_GEODNET_DEBUG`.

## Consequences

- OpenAPI remains the source of truth at runtime (`/docs`).
- Version prefix `/v1` allows breaking changes under `/v2` without silent client breakage.
- `fusion=true` currently returns an explicit telemetry-backed `rtk_v1` evidence contract. It does not claim centimeter-class rover correction until real rover GNSS observations are present.
