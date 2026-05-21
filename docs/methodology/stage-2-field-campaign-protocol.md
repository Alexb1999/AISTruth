# Stage 2 field campaign protocol — AIS vs onboard GNSS

> **Parent doc:** [Validation and ground truth](./validation-and-ground-truth.md) (Stage 2).  
> **Goal:** Collect one publishable dataset comparing **AIS reported positions** to **survey-grade GNSS on the vessel**, plus AISTruth validation evidence and GEODNET context.  
> **Status:** Draft protocol — complete **before** leaving shore.

---

## 1. Campaign summary

| Item | Recommendation |
|------|----------------|
| **Geography** | Norwegian coastal waters with GEODNET density (e.g. Oslofjord → Skagerrak, or Trondheim → Ålesund segment) |
| **Duration** | ≥ 4 h underway + ≥ 30 min stationary (anchorage or berth) |
| **Vessel** | Partner vessel with **Class A AIS**; permission to log MMSI in publication |
| **Ground truth** | Dual-frequency GNSS receiver on board logging **RINEX 3** + NMEA solution stream |
| **AIS reference** | BarentsWatch historic track for same MMSI + optional independent AIS capture |
| **AISTruth** | `/v1/validate/{mmsi}` with `geodnet_probe=true`, `fusion=true`; store full JSON responses |
| **Primary metric** | Horizontal error \( e_h \) (metres) between time-aligned AIS and GNSS fix at each epoch |

**Not in scope for Campaign 1:** satellite imagery, cm-class RTK fusion claims, multi-vessel port-wide screening.

---

## 2. Pre-registration (do before field day)

Write a one-page **analysis plan** and date-stamp it (repo commit or internal note):

1. **Hypotheses** (from parent doc): H1 bounded AIS error in coastal transit; H2 flag correlation exploratory.  
2. **Primary endpoints:** median \( e_h \), 95th percentile \( e_h \), max \( e_h \) — stratified by speed quartile and GEODNET baseline km.  
3. **Exclusions:** segments with GNSS fix type `NONE` / `SINGLE`; AIS gaps > 10 min.  
4. **Sample size:** target ≥ 500 aligned epoch pairs (typically achievable in 4 h at 1 Hz GNSS and ~30 s AIS).  
5. **Publication intent:** technical report / short paper; anonymise MMSI if partner requires (`MMSI_REDACTED` in public bundle).

This reduces post-hoc fishing and strengthens credibility.

---

## 3. Equipment checklist

### 3.1 Required

| # | Item | Notes |
|---|------|--------|
| 1 | **GNSS receiver** (dual-frequency) | u-blox F9P, Emlid Reach RS2+, Septentrio mosaic, or survey-grade equivalent |
| 2 | **Antenna** | Mounted with clear sky view; **measure phase centre offset** to AIS antenna if possible (metres, fore/aft/starboard) |
| 3 | **Logging laptop / SBC** | Raspberry Pi 4+ or rugged laptop; UTC synced via NTP or GNSS time |
| 4 | **Logging software** | `str2str`, RTKLIB `str2str`, Emlid Flow, or vendor app → **RINEX 3 OBS** + **NMEA GGA/GST** |
| 5 | **AIS identity** | Record **MMSI**, vessel name, AIS class (A/B), stated AIS reporting interval |
| 6 | **Mobile internet** | For live NTRIP probe / validate API calls (optional but recommended) |
| 7 | **GEODNET NTRIP credentials** | Rover trial or subscription; same creds as API `geodnet_probe` |
| 8 | **AISTruth API access** | Tenant key; `DATABASE_URL` if persisting runs |

### 3.2 Strongly recommended

| # | Item | Notes |
|---|------|--------|
| 9 | **External AIS receiver** (SDR + rtl_ais, or dedicated AIS dongle) | Independent AIS log decoupled from vessel transponder — detects onboard vs broadcast lag |
| 10 | **GoPro / phone photos** | Berth start/end, antenna mount — metadata only, not positioning |
| 11 | **Barometer / IMU** | Optional; future motion cross-check |
| 12 | **USB GNSS backup** | Second logger for redundancy |

### 3.3 Software versions (record in field log)

- RTKLIB / str2str version  
- AISTruth `rules_version` from validate response  
- GEODNET caster host/mount used  
- Python env for post-processing (`pyproject` lock or `uv pip freeze`)

---

## 4. Route and segment design

Design **three segment types** in one day:

| Segment | Duration | Purpose |
|---------|----------|---------|
| **S1 — Berth / anchor** | 30 min | Stationary AIS drift, freeze heuristics, low-speed error floor |
| **S2 — Coastal transit** | 3–4 h | Primary error distribution; varying speed; multiple GEODNET baselines |
| **S3 — Approach / narrow channel** (optional) | 30 min | Higher manoeuvring; optional radar/VTS cross-check if port cooperative |

**Log segment boundaries** in `field_log.csv` (see §7) with UTC timestamps and short notes (speed, traffic, weather).

**Weather:** Record wind, sea state, precipitation — heavy multipath affects GNSS and invalidates segments if not flagged.

---

## 5. Time synchronisation procedure

AIS timestamps and GNSS logs **must** be traceable to UTC.

### 5.1 Before departure

1. Set logging laptop timezone to **UTC** (display only; files must use UTC internally).  
2. Confirm NTP sync or that GNSS receiver stamps UTC in RINEX/NMEA.  
3. Note **AIS latency**: many systems report `msgtime` = time of fix, not time of transmission (document in field log).

### 5.2 Alignment method (post-processing)

For each AIS report at time \( t_a \):

1. Find bracketing GNSS fixes \( t_g^- \leq t_a \leq t_g^+ \).  
2. If \( t_g^+ - t_g^- > \Delta t_{\max} \) (default **5 s**), skip pair.  
3. **Interpolate** GNSS lat/lon linearly in time (acceptable for slow vessels; for publication also run great-circle interpolation and report Δ < 1 m difference).  
4. Apply **antenna offset** correction if AIS and GNSS antennas are separated (> 2 m): rotate offset by course over ground.

### 5.3 Leap seconds and gaps

- Drop GNSS epochs with fix quality below threshold (see §6.2).  
- Drop AIS duplicates at identical timestamp.  
- Document maximum allowed AIS gap (default **600 s**) for continuous segment analysis.

---

## 6. Data products and file layout

After the campaign, assemble one directory:

```text
campaigns/
  YYYY-MM-DD_<slug>/          # e.g. 2026-06-15_oslofjord-pilot
    README.md                 # MMSI redaction note, participants, consent
    field_log.csv             # segment markers, weather, equipment
    ais/
      barentswatch_track.json # from GET /v1/ais/norway/track/{mmsi}
      external_ais.nmea       # optional raw NMEA from SDR
    gnss/
      rover.obs               # RINEX OBS (3.04+)
      rover.nav               # RINEX NAV (or download IGS final)
      solution.nmea           # GGA + GST if available
      ppk_solution.csv        # post-processed lat, lon, fix_type, pdop, utc
    aistruth/
      validate_<window>.json  # full API responses per window
      ntrip_probe.json        # if captured separately
    analysis/
      aligned_epochs.parquet  # output of skeleton script
      summary_stats.json
      figures/                # histograms, track overlay PNG
```

**Do not commit** raw RINEX or partner MMSI to public Git without consent — use `.gitignore` or private storage.

---

## 7. Field log template (`field_log.csv`)

```csv
utc_time,event,segment,notes
2026-06-15T08:00:00Z,start,S0,Equipment check; NTP synced
2026-06-15T08:15:00Z,gnss_log_start,S1,RINEX file rover_20260615_0815.obs
2026-06-15T08:20:00Z,segment_start,S1,At berth Horten; stationary
2026-06-15T08:50:00Z,segment_end,S1,Depart berth
2026-06-15T08:55:00Z,segment_start,S2,Coastal transit southbound
2026-06-15T12:10:00Z,segment_end,S2,Enter anchorage
2026-06-15T12:15:00Z,segment_start,S1,At anchor 30 min
2026-06-15T12:45:00Z,segment_end,S1,
2026-06-15T12:50:00Z,gnss_log_stop,,End RINEX
2026-06-15T13:00:00Z,aistruth_validate,,Fetched validate JSON windows
```

---

## 8. Field day runbook

### T−7 days

- [ ] Confirm partner vessel, insurance, and permission to publish track shape  
- [ ] Confirm GEODNET NTRIP and AISTruth API keys  
- [ ] Charge batteries; test antenna mount  
- [ ] Dry-run logging 30 min on dock  

### T−1 day

- [ ] Check ephemeris / download forecast NAV if offline PPK  
- [ ] Pre-fetch BarentsWatch token; verify MMSI appears in feed  
- [ ] Pack checklist §3  

### Hour 0 — Setup (30 min)

- [ ] Mount GNSS antenna; photograph mount  
- [ ] Start RINEX + NMEA log; verify UTC timestamps  
- [ ] Record MMSI, offsets, equipment serials in field log  
- [ ] Optional: start external AIS log  

### Hour 0–4 — Underway

- [ ] Mark segment boundaries in field log  
- [ ] Every 30 min: note fix type (RTK fixed / float / single), PDOP if visible  
- [ ] Avoid unnecessary RF interference near antenna  

### Hour 4+ — Wrap

- [ ] 30 min stationary segment  
- [ ] Stop GNSS log; verify file not truncated  
- [ ] Call `GET /v1/validate/{mmsi}?geodnet_probe=true&fusion=true` for campaign window; save JSON  
- [ ] Optional: export BarentsWatch track for full window  
- [ ] Backup all files to second medium  

### T+1 day — Office

- [ ] Run PPK if needed (RTKLIB `rnx2rtkp` or Emlid Studio)  
- [ ] Run analysis skeleton (§10)  
- [ ] Archive raw data; write draft results paragraph  

---

## 9. GNSS quality thresholds

Use for filtering ground-truth epochs:

| Fix type | Use in primary analysis? |
|----------|-------------------------|
| RTK fixed (`QUAL=4` in GGA or solution Q=1) | **Yes** — primary |
| RTK float / DGNSS | Secondary sensitivity analysis only |
| Single-point / autonomous | **Exclude** from primary (report separately) |

Record **PDOP / GST** when available. Exclude epochs with PDOP > 4 for primary stats (document cutoff).

**Expected ground-truth accuracy (order of magnitude):**

- RTK fixed: **0.02–0.10 m** horizontal (conditions dependent)  
- AIS Class A typical: **1–10 m** (ITU/system dependent)  
- Therefore campaign should show **AIS error >> GNSS error** — if not, debug sync or antenna offset.

---

## 10. Analysis pipeline

### Step 1 — PPK / solution CSV

Produce `gnss/ppk_solution.csv`:

```csv
utc,lat,lon,fix_type,pdop,h_acc_m
2026-06-15T08:20:01Z,59.123456,10.456789,fixed,1.2,0.04
```

### Step 2 — AIS normalisation

Parse BarentsWatch or NMEA into:

```csv
utc,mmsi,lat,lon,source
```

### Step 3 — Alignment + error

Run `backend/scripts/analyze_field_campaign.py` (skeleton below) or Jupyter copy to produce `aligned_epochs.parquet`:

| Column | Description |
|--------|-------------|
| `utc` | AIS epoch (UTC) |
| `ais_lat`, `ais_lon` | Reported position |
| `gnss_lat`, `gnss_lon` | Interpolated ground truth |
| `e_h_m` | Haversine horizontal error (m) |
| `segment` | S1 / S2 / S3 |
| `baseline_km` | From validate evidence if available |
| `speed_kn` | Implied from GNSS or AIS |
| `flags` | AISTruth flags if joined |

### Step 4 — Summary statistics

Report at minimum:

- N aligned pairs  
- median, mean, p95, max of `e_h_m` (overall and by segment)  
- Correlation: max implied speed vs flags (exploratory)  
- Overlay map: AIS vs GNSS track  

### Step 5 — AISTruth join

For each AIS window, compare API `confidence_score`, `flags`, `spoofing_findings` against local computation — verifies production parity with `aistruth_core`.

---

## 11. Success criteria (Campaign 1)

| Criterion | Target |
|-----------|--------|
| Aligned epoch pairs | ≥ 500 |
| RTK fixed fraction | ≥ 60% of transit segment |
| Median \( e_h \) documented | Value reported with CI (bootstrap) |
| API parity | Local haversine matches `max_implied_speed_knots` in evidence |
| Reproducible bundle | Another researcher can rerun skeleton script on published subset |

**Failure modes to document honestly:** multipath in fjords, AIS reporting gaps, NTRIP outage, no RTK fix — still publishable as limitations.

---

## 12. Legal and ethics

- **Partner consent** for MMSI, track publication, and photos.  
- **BarentsWatch / AIS terms** — comply with redistribution limits; publish **derived statistics** and degraded tracks if raw AIS cannot be shared.  
- **GEODNET terms** — correction data not redistributed; only metadata (baseline km, byte counts).  
- **Safety** — field work must not distract bridge team; one dedicated crew contact for logging.

---

## 13. Publication checklist

After analysis:

- [ ] Technical report PDF (8–12 pages): methods, map, error histogram, limitations  
- [ ] Public artifact: `summary_stats.json` + one anonymised track figure  
- [ ] Update [validation-and-ground-truth.md](./validation-and-ground-truth.md) §Stage 2 with “Campaign 1 completed” pointer  
- [ ] Optional: submit abstract to ION GNSS+ / Oceans / ENC  
- [ ] **Do not claim** RTK fusion improved position until Layer C solver exists  

---

## 14. Related files

- Analysis skeleton script: [`backend/scripts/analyze_field_campaign.py`](../../backend/scripts/analyze_field_campaign.py)  
- NTRIP smoke test: [`backend/scripts/ntrip_smoke.py`](../../backend/scripts/ntrip_smoke.py)  
- [ADR-002 RTK fusion](../adr/002-rtk-fusion-library.md)
