# ADR 004: Tenant identity and usage metering

## Status

Accepted.

## Context

Phase 1 pilots need named customers, revocable API keys, and validation quotas before Stripe or full SSO. ADR-003 covered static env keys only.

## Decision

- **`tenants`** — slug, `ais_source`, optional BYOK fields (`spire_api_key`, `file_replay_path`), optional `pilot_ends_at`.
- **`api_keys`** — SHA-256 hash of secret; raw key shown once at provisioning.
- **`usage_events`** — append-only row per validate (and bulk inherits per-MMSI validate logs).
- **`validation_runs.tenant_id`** — nullable FK; history scoped to tenant when authenticated via DB key.
- **Auth order:** DB key → tenant; else env `AISTRUTH_API_KEYS`; else auth disabled (local dev).
- **`GET /v1/me`** — tenant slug + ais_source for console.
- **`GET /v1/admin/usage`** — month-to-date units; requires `X-Admin-Key` / `AISTRUTH_ADMIN_KEY`.
- **AIS ingest** — `fetch_ais_reports()` selects BarentsWatch, Spire BYOK, or file replay from tenant override or deployment settings.

## Consequences

- Env keys remain for bootstrap; production pilots should use `scripts/create_pilot_tenant.py`.
- Spire keys in DB are plain text at pilot stage — move to secret manager before multi-tenant production.
- Watchlist table exists for Phase 3; no HTTP routes yet.
