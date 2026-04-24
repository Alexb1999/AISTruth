# BarentsWatch (Norwegian open AIS) — Phase 1 engine feed

AISTruth uses the **Norwegian Coastal Administration** open AIS dataset exposed via **BarentsWatch** as the default **development** AIS source. Coverage is **Norwegian waters** (EEZ / defined zones), not the Canadian Maritimes, but licensing and API quality make it the recommended **gold standard** for building the fusion and time-alignment engine before you attach Canadian or customer-paid feeds.

## Official references

- Developer overview: [Live AIS API](https://developer.barentswatch.no/docs/AIS/live-ais-api/)
- Examples (token, latest, tracks, streaming): [Example requests](https://developer.barentswatch.no/docs/AIS/examples/)
- Register a user at [barentswatch.no](https://www.barentswatch.no/), then create an **API client** on **MyPage** with OAuth2 **client credentials** and scope **`ais`**.

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

- `GET /v1/ais/norway/track/{mmsi}` — last **24 hours** of positions for one MMSI (historic endpoint).
- `GET /v1/ais/norway/latest?mmsi=…&mmsi=…` — **latest** snapshot for one or more MMSIs (live endpoint).

Responses are JSON arrays of `{ mmsi, time, lat, lon }` in **UTC** (`time` is ISO-8601).

## Product note

Treat redistribution and commercial use of raw or derived AIS according to **BarentsWatch / Kystverket terms** at the time you ship. For **Canadian Maritimes** product narratives, plan a second adapter (customer feed, receiver, or licensed aggregator) while keeping Norway for **R&D parity** and regression tests.

For the RTK side of fusion, see [geodnet-rtk.md](geodnet-rtk.md) and `scripts/ntrip_smoke.py`.
