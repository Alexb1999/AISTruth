# ADR 003: API auth and rate limiting

## Status

Accepted.

## Context

Validation routes call upstream AIS services and may open GEODNET NTRIP sessions. Those calls need basic protection before staging or public demos.

## Decision

- Protect `/v1/*` routes with optional `X-AIS-Key` auth when `AISTRUTH_API_KEYS` is configured.
- Leave `/health` public for infrastructure checks.
- Apply per-key or per-IP rate limits using SlowAPI:
  - `GET /v1/validate/{mmsi}`: `30/minute`.
  - `POST /v1/validate/bulk`: `10/minute`.
  - `GET /v1/debug/geodnet-ntrip`: `6/minute`.
  - `POST /v1/geodnet/sync-stations`: `12/minute`.
  - `GET /v1/ais/norway/vessels`: `10/minute` per tenant/key (proxies BarentsWatch “all vessels” snapshot; cached 5 min by default).
- When `BARENTSWATCH_*` credentials are set, **all BarentsWatch upstream calls require a valid `X-AIS-Key`** (DB tenant or `AISTRUTH_API_KEYS`), unless `AISTRUTH_BARENTSWATCH_ALLOW_ANONYMOUS=true` (local dev only).
- Norway proxy routes (`/v1/ais/norway/*`) additionally require `ais_source=barentswatch` for the caller.
- Emit `X-Request-ID` on responses and JSON logs for traceability.

## Consequences

- Local development remains simple when `AISTRUTH_API_KEYS` is empty.
- Staging and production can use static API keys until a customer identity provider is justified.
- NTRIP debug routes are less likely to exhaust external caster or API resources accidentally.
