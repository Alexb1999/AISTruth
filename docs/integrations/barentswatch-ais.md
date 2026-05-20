# BarentsWatch (Norwegian open AIS) — Phase 1 engine feed

AISTruth uses the **Norwegian Coastal Administration** open AIS dataset exposed via **BarentsWatch** as the default **development** AIS source. Coverage is **Norwegian waters** (EEZ / defined zones), not the Canadian Maritimes, but licensing and API quality make it the recommended **gold standard** for building the fusion and time-alignment engine before you attach Canadian or customer-paid feeds.

## Official references

- Developer overview: [Live AIS API](https://developer.barentswatch.no/docs/AIS/live-ais-api/)
- Examples (token, latest, tracks, streaming): [Example requests](https://developer.barentswatch.no/docs/AIS/examples/)
- Register a user at [barentswatch.no](https://www.barentswatch.no/), then create an **API client** on **MyPage** with OAuth2 **client credentials** and scope **`ais`**.

## First-time setup (checklist)

1. **Account:** Sign up / log in at [barentswatch.no](https://www.barentswatch.no/) (Norwegian/English as offered).
2. **API client:** Open **MyPage** (Min side) and create an **API client** using the **client credentials** (machine-to-machine) flow — not a “public app” redirect flow unless that is what their portal offers for AIS.
3. **Scope:** Ensure the client is allowed to request scope **`ais`** (exactly that string). If the portal lets you tick API products or scopes, enable **AIS** / **Live AIS** per their UI.
4. **Copy secrets:** Note the **client id** and **client secret**; the secret is often shown only once.
5. **Local env:** From the repo, copy `backend/.env.example` to `backend/.env` and set `BARENTSWATCH_CLIENT_ID` and `BARENTSWATCH_CLIENT_SECRET`.
6. **Run API from `backend`:** The app loads `.env` from the current working directory (`Settings` uses `env_file=".env"`). Example: `cd backend && uvicorn main:app --reload`.
7. **Smoke-test token:**

```bash
curl -sS -X POST https://id.barentswatch.no/connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "client_id=$BARENTSWATCH_CLIENT_ID" \
  --data-urlencode "client_secret=$BARENTSWATCH_CLIENT_SECRET" \
  --data-urlencode 'scope=ais' \
  --data-urlencode 'grant_type=client_credentials'
```

You should see JSON with an `access_token`. If you see `invalid_client`, the id/secret are wrong. If you see `invalid_scope`, the client is not permitted to use `ais` — go back to MyPage and fix the client configuration.

8. **Smoke-test data:** BarentsWatch’s own docs use MMSI **257111020** for a historic track example (Norwegian waters). Try:

```bash
# After exporting TOKEN from the JSON above:
curl -sS "https://historic.ais.barentswatch.no/v1/historic/trackslast24hours/257111020" \
  -H "Authorization: Bearer $TOKEN"
```

Empty array `[]` can mean **no positions in the last 24h** for that MMSI in their open dataset (not necessarily a broken integration). A **404** from the upstream API often means **no track** for that vessel in the window.

9. **AISTruth routes:** With the same env vars on the API process, call `GET http://127.0.0.1:8000/v1/ais/norway/track/257111020` (or your MMSI), `GET /v1/ais/norway/vessels` for a **pick list of live MMSIs** (no MarineTraffic), and `GET /docs` for OpenAPI.

### Client ID shape (what My clients shows)

Self‑registered BarentsWatch clients often use a **full client id** like `yourname@example.com:MyClient` (email, colon, then the client name you chose). That string is **correct** — copy it from the **Client ID** field in My clients. The portal also shows **Client ID urlencoded** (`%40` for `@`, `%3A` for `:`, `%20` for space); use that form only when a tool asks for “URL-encoded client id” and you are **not** re-encoding it again (see [Application registration](https://developer.barentswatch.no/docs/appreg/)).

### Token errors

**`{"error":"invalid_request"}`** is often a **format / quoting** problem, not “wrong account”:

- **Quote `client_id` in `.env`** if it contains spaces or special characters, e.g.  
  `BARENTSWATCH_CLIENT_ID="you@example.com:AISTruth API"`  
  An unquoted line can be parsed incorrectly so the id or secret is truncated or split.
- **`client_secret`:** Under **Client secrets**, open the **Created …** entry and copy the **secret value** the UI shows. That is what belongs in `BARENTSWATCH_CLIENT_SECRET` (it is the secret you created for that row; if you rotated secrets, use the current one).
- **Shell vs `.env`:** `curl` does not read `.env` by itself. Either `export` both variables in the same terminal, or run `set -a && source backend/.env && set +a` before `curl` (zsh/bash).
- **If it still fails**, try sending the portal’s **urlencoded** id **once**, without letting curl encode it again (so the `%` signs are not doubled):

```bash
curl -sS -X POST https://id.barentswatch.no/connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "scope=ais" \
  --data-urlencode "client_secret=$BARENTSWATCH_CLIENT_SECRET" \
  --data "client_id=PASTE_CLIENT_ID_URLENCODED_FROM_PORTAL"
```

(replace the value with the **Copy** button under **Client ID urlencoded** in My clients).

Avoid smart quotes when pasting. See also [Using the OpenAPI documentation](https://developer.barentswatch.no/docs/usingopenapi/) — for some tools they require the **URL-encoded** client id.

**`invalid_client`** → wrong id/secret. **`invalid_scope`** → client not allowed to use scope `ais` (adjust permissions in MyPage).

### Coverage reality check

Open AIS via BarentsWatch is limited to **Norwegian economic zone and related areas** (see the map on the [Live AIS API](https://developer.barentswatch.no/docs/AIS/live-ais-api/) page). Vessels that only sail outside that area, or classes excluded from open data (e.g. small fishing / leisure rules), may return **no points** even when your credentials are correct.

## Environment variables

Set these in your shell or `.env` (never commit secrets):

| Variable | Purpose |
|----------|---------|
| `BARENTSWATCH_CLIENT_ID` | OAuth2 client id |
| `BARENTSWATCH_CLIENT_SECRET` | OAuth2 client secret |

Token endpoint (client credentials):

```bash
curl -X POST https://id.barentswatch.no/connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'client_id=YOUR_CLIENT_ID' \
  --data-urlencode 'client_secret=YOUR_CLIENT_SECRET' \
  --data-urlencode 'scope=ais' \
  --data-urlencode 'grant_type=client_credentials'
```

## AISTruth API routes (this repo)

With credentials set, the FastAPI app exposes:

- `GET /v1/ais/norway/vessels` — short **vessel picker** list (live snapshot; rate-limited and cached server-side).
- `GET /v1/ais/norway/track/{mmsi}` — last **24 hours** of positions for one MMSI (historic endpoint).
- `GET /v1/ais/norway/latest?mmsi=…&mmsi=…` — **latest** snapshot for one or more MMSIs (live endpoint).

**Access control:** When `BARENTSWATCH_*` is configured on the server, these routes (and validate when `ais_source=barentswatch`) require a valid **`X-AIS-Key`** — DB tenant key or `AISTRUTH_API_KEYS` operator key. Norway browse is limited to **`ais_source=barentswatch`** tenants. Set `AISTRUTH_BARENTSWATCH_ALLOW_ANONYMOUS=true` only for isolated local dev.

Responses are JSON arrays of `{ mmsi, time, lat, lon }` in **UTC** (`time` is ISO-8601).

## Product note

Treat redistribution and commercial use of raw or derived AIS according to **BarentsWatch / Kystverket terms** at the time you ship. For **Canadian Maritimes** product narratives, plan a second adapter (customer feed, receiver, or licensed aggregator) while keeping Norway for **R&D parity** and regression tests.

For the RTK side of fusion, see [geodnet-rtk.md](geodnet-rtk.md) and `scripts/ntrip_smoke.py`.
