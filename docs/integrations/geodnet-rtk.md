# GEODNET RTK / NTRIP — integration notes (AISTruth)

This document supports **Phase 2** work: receiving RTCM corrections and later fusing them with AIS. Keep it updated when GEODNET changes endpoints or terms.

## Official references

| Topic | Link |
|--------|------|
| **NTRIP service behaviour** (mountpoints, GGA requirement, RTCM 3.2 MSM, troubleshooting) | [geodnet/GEODNET_RTK_SERVICE](https://github.com/geodnet/GEODNET_RTK_SERVICE) |
| **Sample NTRIP client** (conceptual checklist) | [geodnet/ntrip](https://github.com/geodnet/ntrip) |
| **RTK REST API** (account/coverage/station list, `appId` / `appKey` signing) | [GEODNET_RTK_API.md](https://github.com/geodnet/GEODNET_API/blob/main/GEODNET_RTK_API.md) |
| **Hosted RTK docs** | [RTK Docs Center](https://rtkdocs.geodnet.com/rtk-service/quick-start) |
| **Coverage map** | [https://rtk.geodnet.com/](https://rtk.geodnet.com/) |
| **Station map** | [https://rtk.geodnet.com/map](https://rtk.geodnet.com/map) |

## Trial vs paid vs enterprise

- **Rover trial:** Request via [GEODNET free RTK trial](https://geodnet.com/free) / [Quick Start](https://rtkdocs.geodnet.com/rtk-service/quick-start). You receive **NTRIP username + password** (and possibly region-specific host guidance—follow the email).
- **Ongoing RTK:** Typically a **paid subscription** after trial (see GEODNET and reseller pages for current pricing).
- **Enterprise RTK API:** Separate **`appId` / `appKey`** flow for provisioning many users—see `GEODNET_RTK_API.md`. Do not assume it is included in a single-rover trial.

## NTRIP connection (typical)

Defaults below match common GEODNET documentation; **confirm host/port in your trial email** if they differ.

| Setting | Common default | Notes |
|---------|----------------|--------|
| Host | `rtk.geodnet.com` | Regional AWS endpoints may exist—use what GEODNET provides. |
| Port | `2101` | NTRIP over TCP. |
| Mountpoint | `AUTO` (or `AUTO_ITRF2020`, `AUTO_WGS84`, …) | See mountpoint table in `GEODNET_RTK_SERVICE`. |
| Auth | HTTP **Basic** (`username:password` Base64) | Standard NTRIP. |

## Critical: NMEA GGA

The caster expects your client to **send periodic GGA** sentences (approximate rover position). Without valid GGA, you may see **no RTCM** or an error close—see GEODNET troubleshooting table.

For **cloud / simulated rover** development, generate GGA at a fixed coordinate (e.g. Oslofjord entrance used for your trial request) until a live GNSS engine feeds real GGA.

## Local smoke test (this repo)

With trial credentials in the environment:

```bash
source .venv/bin/activate   # or your venv
export GEODNET_NTRIP_USER='...'
export GEODNET_NTRIP_PASSWORD='...'
python scripts/ntrip_smoke.py --seconds 20
```

If you already store secrets in `apps/api/.env` (same variable names), you can load them without `export`:

```bash
python scripts/ntrip_smoke.py --env-file apps/api/.env --seconds 20
```

The loader **does not override** variables already present in your shell.

The script prints header diagnostics, **total bytes read**, and how many **RTCM3** frames (payloads starting with `0xD3`) were observed. It does **not** decode MSM5 yet—that comes in the fusion milestone.

## FastAPI integration (this repo)

When the API process has the same env vars in `apps/api/.env` (or the environment), you can probe from HTTP:

- **`GET /v1/debug/geodnet-ntrip?seconds=5`** — short NTRIP session using **`GEODNET_SMOKE_LAT` / `GEODNET_SMOKE_LON`** (defaults: Oslofjord entrance); returns JSON telemetry (`bytes_total`, `rtcm_frame_count`, `rtcm_message_counts`, etc.). Registered only when **`AISTRUTH_ENABLE_GEODNET_DEBUG=true`** on the API process. **Local/dev** only.

- **`GET /v1/validate/{mmsi}?geodnet_probe=true&geodnet_probe_seconds=4`** — same AIS validation as before, plus an optional **`evidence.geodnet_ntrip_probe`** block. GGA is sent at the **latest AIS position** in the filtered window (better alignment than a fixed coordinate).

`rtcm_message_counts` keys are decimal RTCM message numbers as strings (plus `"-1"` if the 12-bit header could not be read). CRC is **not** verified; counts are health/telemetry, not legal proof of MSM content.

## Station catalog sync (RTK REST API)

Enterprise deployments can obtain **`appId`** and **`appKey`** from GEODNET (see `GEODNET_RTK_API.md`). With Postgres running and **`DATABASE_URL`** set:

1. Run Alembic through revision **`20260517_0003`** so `geodnet_nodes` has `ingest_source`, `station_status`, and `synced_at`.
2. Set **`GEODNET_RTK_APP_ID`** and **`GEODNET_RTK_APP_KEY`** in the API environment.
3. Call **`POST /v1/geodnet/sync-stations`** (same auth as other `/v1/*` routes when `AISTRUTH_API_KEYS` is set).

The handler calls **`POST {GEODNET_RTK_API_BASE}/api/v3/station/list`** with the vendor **MD5 sign** algorithm, then upserts rows with **`id = geodnet:<station name>`**, **`ingest_source = geodnet_rtk_api`**, and **`active`** derived from status (`ACTIVE` / `ONLINE` vs `OFFLINE`). **Fixture/demo rows** (`ingest_source='fixture'`) are never deleted by this job.

Optional:

- **`GEODNET_RTK_STATION_REGION`** — ISO 3166-1 alpha-3 country filter when the API supports it (e.g. `NOR`).
- **`GEODNET_SYNC_STATIONS_AT_STARTUP=true`** — best-effort sync when the API bootstraps (logs a warning on failure).

## Product / compliance

- Store **NTRIP credentials** only in env or a secret manager; never commit.
- Treat **redistribution** of raw RTCM or derived corrections per GEODNET’s current terms.
- For multi-tenant SaaS, plan **BYOK** or **customer-contracted** RTK seats so you are not the sole bearer of correction-network COGS.
