# ⚓ AISTruth

> **The Source of Truth for Maritime Positioning.**

[License: MIT](https://opensource.org/licenses/MIT)](https://img.shields.io/badge/License-MIT-blue.svg)]([https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)))

[Stack: Next.js + FastAPI](https://nextjs.org/)](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI-black)]([https://nextjs.org/](https://nextjs.org/)))

[Network: GEODNET](https://geodnet.com/)](https://img.shields.io/badge/Network-GEODNET-orange)]([https://geodnet.com/](https://geodnet.com/)))

## 🌊 The Mission

Standard AIS data is "noisy" and vulnerable. **AISTruth** provides a high-fidelity verification layer by fusing global AIS streams with local GEODNET RTK (Real-Time Kinematic) corrections. We turn 5-meter uncertainty into 2-centimeter certainty.

## 🚀 Key Capabilities

- **RTK-Corrected AIS:** Apply centimeter-level ground truth to coastal vessel traffic.
- **Spoofing Guard:** Detect GNSS manipulation by cross-referencing vessel reports with local ionospheric noise profiles.
- **Integrity Scoring:** A proprietary "Trust Score" for vessels in coastal validation zones wherever GEODNET coverage supports fusion.
- **Cloud-First:** Fuse AIS with the public GEODNET network—no owned miner or coastal "super node" required to ship the MVP.

## 📄 Documentation

- [Master scope & architecture](docs/AISTruth_Master_Scope.md): cloud-first SaaS blueprint, GEODNET fusion gaps, branching (`dev` / `stg` / `prod`), roadmap, and monetization.

## 🏗 Project Structure

- `apps/web`: Next.js dashboard for real-time geospatial visualization.
- `apps/api`: FastAPI backend handling NTRIP streams and AIS decoding.
- `packages/core`: The "Truth Engine" logic—math for coordinate correction and anomaly detection.
- `hardware` (optional/future): Notes for any proprietary ground station; not required for the core SaaS path.

## 🛠 Tech Stack

- **Languages:** Python (Data Science/API), TypeScript (Frontend).
- **Frameworks:** FastAPI, Next.js 14, Tailwind CSS.
- **Geospatial:** PostGIS, Leaflet/Mapbox, `pyais`, `gnss-lib-py`.

---

*Built by Alex Boutilier | Maritime Data Science & DePIN Infrastructure*