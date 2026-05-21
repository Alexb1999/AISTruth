# AIS integrity validation — scientific methodology and ground truth

> **Purpose:** Define how AISTruth proves (and does not overclaim) that its validation and correction-evidence pipeline works. Use this document to plan benchmarks, pilots, and publishable results.
>
> **Status:** Living draft (May 2026). Aligns with [ADR-002 RTK fusion](../adr/002-rtk-fusion-library.md) and current `rules_version` in `aistruth_core.scoring`.

---

## 1. What we are actually validating (three layers)

AISTruth is **not** a single “position truth” product today. Treat validation as three separable claims:

| Layer | Question | Current MVP | Requires ground truth? |
|-------|----------|-------------|----------------------|
| **A — Track plausibility** | Does the AIS time series obey physics and reporting consistency? | Yes — haversine implied speed, monotonic time, freeze/jump heuristics (`track_heuristics`, `spoofing`) | No (self-consistency) |
| **B — Reference geometry** | Is a GEODNET correction reference reachable at the reported fix? | Yes — nearest-node distance, K-nearest map context, optional NTRIP probe (RTCM byte telemetry) | Partially (proves caster reachability, not vessel position) |
| **C — Position refinement** | What is the vessel’s true position after applying RTK? | **Not yet** — `RtkFusionEngine` returns `telemetry_only_rover_observations_unavailable` until rover GNSS observations exist | **Yes** — always |

**Publishable today:** Layers A and B with explicit limits.  
**Do not publish cm-class accuracy claims** until Layer C is implemented with rover observations and Layer C is benchmarked against ground truth.

---

## 2. Ground truth — what counts, and what does not

Ground truth is an **independent estimate of vessel position at time *t*** with known error budget, used to score AIS (and later fused) positions.

### 2.1 Gold standard (use for scientific proof)

1. **Survey-grade GNSS on the vessel under test**  
   - Dual-frequency RTK/PPK receiver logging RINEX + solution (e.g. RTKLIB, gnss-lib-py).  
   - Expected horizontal accuracy: **cm–dm** in fixed solution, **dm–m** in float, documented PDOP/fix type.  
   - This is the correct ground truth for “AIS vs real position” and for any future “RTK correction improved position by X metres.”

2. **Independent terrestrial RF references (fixed)**  
   - Coast guard / VTS radar plot, laser/radar range from known structure, or port AIS base station with surveyed antenna position.  
   - Useful for **approach channels and ports**; accuracy typically **m–10 m** depending on system.

3. **High-trust AIS from vessel-owned Class A transponder + surveyed install**  
   - Only ground truth for **other vessels’ AIS** if the reference vessel’s antenna position is surveyed and time sync is verified.  
   - Weak alone; strong as part of a multi-sensor campaign.

### 2.2 Silver standard (pilot and operations evidence)

4. **Known anchorage / berth occupancy**  
   - Vessel reported “at berth” vs AIS drift — good for **freeze/spoofing** case studies, not sub-metre proof.

5. **Corridor constraints**  
   - Fairway centreline, dredged channel, AIS historical track density — supports **plausibility**, not calibration.

6. **Public incident / enforcement cases**  
   - Documented spoofing or AIS manipulation with court/agency findings — qualitative validation of **detection** not ranging.

### 2.3 Satellite imagery — do we need it?

**Short answer: No for core mathematical proof. Optional for case studies and communication.**

| Use | Value | Limitation |
|-----|-------|------------|
| **Visual confirmation** that a vessel is roughly where AIS says (harbour, anchorage) | Medium — good for papers and demos | Cloud, night, revisit time; not continuous |
| **Sub-metre position truth** | Poor — ship length scales (~100–400 m); wake/heading ambiguity | Not a positioning instrument |
| **SAR for dark targets** | Niche — research / defence contexts | Cost, latency, expertise; not MVP |
| **Automated AIS–SAR fusion benchmarks** | Emerging research (e.g. academic datasets) | Heavy ML pipeline; license and latency |

**Recommendation:**  
- **Phase 1 benchmarks:** onboard GNSS + optional port radar/VTS, **not** satellite.  
- **Phase 2 publications:** add 1–2 **annotated case studies** with Sentinel-2 / Planet **only** where open data and clear ship signature exist (e.g. moored tanker in clear weather). Label as **supporting evidence**, not primary ground truth.

---

## 3. Proof programme — staged experiments

### Stage 0 — Internal consistency (no ground truth, shippable now)

**Goal:** Prove the **math and code** for Layer A are correct.

| Test | Method | Pass criterion |
|------|--------|----------------|
| Implied speed | Synthetic tracks: known speed, interval, great-circle path | Computed speed within tolerance of analytical value |
| Jump detection | Inject 80 kt leg between two realistic legs | `implausible_speed_over_60kt` fires |
| Freeze detection | Repeat identical lat/lon ≥ N times | `position_freeze` finding |
| Score monotonicity | Degrade track with one bad leg | Confidence score decreases |

**Deliverable:** Unit tests in `packages/core/tests/` + `rules_version` bump in release notes.

**Publication:** Methods section referencing haversine on WGS84 sphere, thresholds (45/60 kt), and explicit non-claim of spoofing **detection rate** without labelled dataset.

---

### Stage 1 — Correction-stream and geometry evidence (Layer B)

**Goal:** Prove we correctly characterize **GEODNET reachability**, not vessel position.

| Test | Method | Pass criterion |
|------|--------|----------------|
| Nearest node | PostGIS `geom <-> point` vs brute-force on fixture set | Same nearest ID |
| Baseline | Compare computed km to geodesic library | Δ < 0.1% |
| NTRIP probe | Live probe at AIS lat/lon with valid credentials | RTCM bytes > 0, message types logged |
| Fusion contract | `fusion=true` | `status=telemetry_only_rover_observations_unavailable`; no cm claim |

**Deliverable:** Reproducible script (`scripts/ntrip_smoke.py`) + logged evidence JSON from `/v1/validate`.

**Publication:** “Correction infrastructure availability index” — distance to reference, correction age, RTCM histogram — **not** “RTK position error.”

---

### Stage 2 — Controlled field campaign (Layer C prerequisite)

**Goal:** First **quantitative** AIS position error statistics vs ground truth.

**Minimum design:**

1. **Platform:** Partner vessel or charter with **dual-frequency GNSS logger** (1 Hz+) + AIS Class A feed (or matched AIS from same voyage in replay).
2. **Route:** Coastal segment with **GEODNET coverage** (Norwegian pilot) or documented baseline length.
3. **Duration:** ≥ 4 hours transit + 30 min stationary (anchorage/berth).
4. **Sync:** UTC time alignment between GNSS solution timestamps and AIS `msgtime` (document interpolation — great-circle or filter — per ADR gap analysis).
5. **Metrics:**
   - Horizontal error: \( e_h = \|\text{AIS} - \text{GNSS}\|_2 \) at aligned epochs  
   - Along-track / cross-track decomposition (optional)  
   - Distribution: median, 95th percentile, max  
   - Stratify by baseline to nearest GEODNET node, speed, and fix interval  

**Hypotheses we can test:**

- H1: AIS position error is **bounded** and stable in open coastal transit (baseline descriptive stats).  
- H2: Implausible-speed flags **correlate** with segments where \( e_h \) or implied dynamics fail plausibility checks (requires labelled bad segments or injected tests).  
- H3: When rover observations + solver ship, fused position reduces \( e_h \) vs raw AIS **in Zone Alpha** (baseline < X km) — **future work**.

**Deliverable:** Dataset (anonymised MMSI optional), analysis notebook, short technical report. Protocol: [stage-2-field-campaign-protocol.md](./stage-2-field-campaign-protocol.md).

---

### Stage 3 — Spoofing and integrity detection benchmark

**Goal:** Publish **detection performance** with labelled data.

| Data source | Labels |
|-------------|--------|
| Synthetic injection | Known jump/freeze/spoof patterns |
| Public research datasets | AIS anomaly papers (cite + license) |
| Partner-provided incident tracks | Expert-labelled segments |

**Metrics:** Precision/recall per finding `kind`, false positive rate on clean coastal traffic (Norway open AIS sample).

**Do not claim** “100% spoof detection” — report operating points and thresholds (`rules_version`).

---

## 4. RTK corrections vs AIS — scientific framing

### What RTK corrections actually are

RTCM streams from GEODNET are **corrections to GNSS observables** at a rover location. They do **not**, by themselves, move an AIS dot.

AIS reports a **self-declared** position (often from the vessel’s own GNSS/AIS unit), with variable accuracy (Class A typically better than Class B), update rate, and latency.

### Valid fusion question (future)

> At time *t*, given rover GNSS observations **O**(*t*), corrections **C**(*t*), and ephemeris, does solver output **P**(*t*) have lower error vs ground truth than AIS report **A**(*t*)?

**Required inputs today:** Missing rover **O**(*t*) — hence ADR-002 telemetry-only status.

### Invalid claim (reject in papers and sales)

> “We applied RTK to AIS and improved position to cm accuracy.”

Without **O**(*t*) and a validated solver, the refined lat/lon in evidence must not be marketed as RTK output.

---

## 5. Mathematical checklist (soundness)

Before any publication, verify:

- [ ] **WGS84** consistency — all lat/lon in decimal degrees; distances via geodesic (haversine acceptable for MVP nm; use Vincenty/geographiclib for publication stats).
- [ ] **Time base** — all timestamps UTC; AIS latency documented; interpolation method stated.
- [ ] **Speed** — knots from nm/h; handle duplicate timestamps and out-of-order reports.
- [ ] **Baseline** — geodesic distance vessel → reference station, not Euclidean on lat/lon.
- [ ] **Score** — bounded [0, 100]; components documented (`combine_motion_and_geodnet_baseline`); version pinned (`RULES_VERSION`).
- [ ] **Uncertainty** — report confidence intervals on field errors, not point claims.
- [ ] **Multiple testing** — if scanning many MMSIs, control false discovery or report exploratory analysis honestly.

---

## 6. Publication roadmap

| Artifact | Audience | Timeline suggestion |
|----------|----------|---------------------|
| **Technical report / white paper** — Layers A+B, honest limits | Customers, regulators | After Stage 0–1 complete |
| **Field benchmark paper** — AIS error vs onboard GNSS | Maritime GNSS / PNT community | After Stage 2 |
| **Open benchmark subset** — anonymised tracks + labels | Research | After Stage 3 |
| **ADR series** (already public) | Engineers | Ongoing |
| **Conference** (ION GNSS+, ENC, MTS/IEEE Oceans) | Academic + industry | Target 12–18 months with Stage 2 data |

**Suggested title direction:** *“Independent integrity evidence for maritime AIS: plausibility scoring, reference-network context, and a path to GNSS-fused validation.”*

---

## 7. What to do next (practical order)

1. **Freeze `rules_version` semantics** — document every flag threshold in this file and in code docstrings.  
2. **Expand core unit tests** — Stage 0 synthetic tracks (already partially in `packages/core/tests/`).  
3. **Plan one Norway field day** — partner vessel + GNSS logger; one port approach; log AIS + RINEX + NTRIP probe metadata.  
4. **Do not buy satellite imagery for MVP proof** — revisit for one visual case study after Stage 2 stats exist.  
5. **Implement rover observation ingest** (ADR-002) before any Layer C accuracy marketing or paper claims.  
6. **Pre-register analysis** (optional) — write Stage 2 protocol before collecting data to strengthen publication credibility. See [stage-2-field-campaign-protocol.md](./stage-2-field-campaign-protocol.md).

---

## 8. References and related docs

- [Stage 2 field campaign protocol](./stage-2-field-campaign-protocol.md)  
- [ADR-002 RTK fusion library path](../adr/002-rtk-fusion-library.md)  
- [GEODNET RTK / NTRIP integration](../integrations/geodnet-rtk.md)  
- [API evidence contract](../adr/001-api-contract-sketch.md)  
- ITU-R M.1371 (AIS technical characteristics) — for AIS accuracy expectations  
- IMO MSC/Circ.289 / AIS integrity guidance — regulatory context  
- RTKLIB / gnss-lib-py — future solver validation toolchain  

---

## 9. Summary answers

| Question | Answer |
|----------|--------|
| Is our **current** validation mathematically sound? | **Layer A yes**, if tests cover haversine, thresholds, and edge cases. **Layer B** geometry is standard geodesy. **Layer C not implemented.** |
| What is **ground truth** for AIS vs real position? | **Survey-grade GNSS on the vessel** (best). Port radar/VTS second. Satellite imagery **not** primary ground truth. |
| Do we **need satellite images**? | **No** for proof. Optional for communication and coarse visual case studies. |
| Can we **publish now**? | Yes — on **methods, telemetry, and plausibility scoring** with explicit limits. Wait for field GNSS campaign before accuracy or RTK improvement claims. |
