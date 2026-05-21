#!/usr/bin/env python3
"""Stage 2 field campaign analysis skeleton — AIS vs onboard GNSS ground truth.

Usage (after filling campaign directory):

    uv run python scripts/analyze_field_campaign.py \\
        --campaign-dir ../campaigns/2026-06-15_oslofjord-pilot \\
        --mmsi 259123456

Inputs (see docs/methodology/stage-2-field-campaign-protocol.md):
    gnss/ppk_solution.csv   — utc, lat, lon, fix_type, pdop, h_acc_m
    ais/barentswatch_track.json — BarentsWatch historic track JSON array
    field_log.csv           — optional segment markers

Outputs:
    analysis/aligned_epochs.parquet
    analysis/summary_stats.json
    analysis/figures/error_hist.png  (if matplotlib installed)

This script is a starting point — adjust paths, fix-type filters, and interpolation
before publication.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Reuse core geodesy for consistency with production scoring.
from aistruth_core.track_heuristics import haversine_nm

M_PER_NM = 1852.0


@dataclass(frozen=True)
class GnssFix:
    t: datetime
    lat: float
    lon: float
    fix_type: str
    pdop: float | None


@dataclass(frozen=True)
class AisFix:
    t: datetime
    lat: float
    lon: float


def parse_utc(value: str) -> datetime:
    s = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def load_gnss_csv(path: Path) -> list[GnssFix]:
    import csv

    rows: list[GnssFix] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                GnssFix(
                    t=parse_utc(row["utc"]),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    fix_type=row.get("fix_type", "unknown").strip().lower(),
                    pdop=float(row["pdop"]) if row.get("pdop") else None,
                )
            )
    return sorted(rows, key=lambda r: r.t)


def load_ais_barentswatch_json(path: Path) -> list[AisFix]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Expected JSON array of AIS points")
    out: list[AisFix] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        t_key = "msgtime" if "msgtime" in row else "time"
        out.append(
            AisFix(
                t=parse_utc(str(row[t_key])),
                lat=float(row["latitude"] if "latitude" in row else row["lat"]),
                lon=float(row["longitude"] if "longitude" in row else row["lon"]),
            )
        )
    return sorted(out, key=lambda r: r.t)


def horizontal_error_m(a: AisFix, g_lat: float, g_lon: float) -> float:
    return haversine_nm(a.lat, a.lon, g_lat, g_lon) * M_PER_NM


def interpolate_gnss(gnss: list[GnssFix], t: datetime) -> GnssFix | None:
    if not gnss:
        return None
    if t < gnss[0].t or t > gnss[-1].t:
        return None
    for left, right in zip(gnss, gnss[1:], strict=False):
        if left.t <= t <= right.t:
            if right.t == left.t:
                return left
            frac = (t - left.t).total_seconds() / (right.t - left.t).total_seconds()
            return GnssFix(
                t=t,
                lat=left.lat + frac * (right.lat - left.lat),
                lon=left.lon + frac * (right.lon - left.lon),
                fix_type=left.fix_type if frac < 0.5 else right.fix_type,
                pdop=left.pdop,
            )
    return None


def align_epochs(
    ais: list[AisFix],
    gnss: list[GnssFix],
    *,
    max_pair_delta_s: float = 5.0,
    allowed_fix_types: frozenset[str] = frozenset({"fixed", "rtk_fixed", "4"}),
    max_pdop: float = 4.0,
) -> list[dict[str, object]]:
    aligned: list[dict[str, object]] = []
    for a in ais:
        g = interpolate_gnss(gnss, a.t)
        if g is None:
            continue
        if g.fix_type not in allowed_fix_types:
            continue
        if g.pdop is not None and g.pdop > max_pdop:
            continue
        # Bracket check: nearest raw GNSS sample within max_pair_delta_s
        nearest_delta = min(abs((a.t - fix.t).total_seconds()) for fix in gnss)
        if nearest_delta > max_pair_delta_s:
            continue
        eh = horizontal_error_m(a, g.lat, g.lon)
        aligned.append(
            {
                "utc": a.t.isoformat(),
                "ais_lat": a.lat,
                "ais_lon": a.lon,
                "gnss_lat": g.lat,
                "gnss_lon": g.lon,
                "e_h_m": eh,
                "fix_type": g.fix_type,
                "pdop": g.pdop,
            }
        )
    return aligned


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    k = (len(ordered) - 1) * p / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return ordered[int(k)]
    return ordered[f] + (ordered[c] - ordered[f]) * (k - f)


def summarise_errors(errors: list[float]) -> dict[str, float | int]:
    if not errors:
        return {"n": 0}
    return {
        "n": len(errors),
        "mean_m": sum(errors) / len(errors),
        "median_m": percentile(errors, 50),
        "p95_m": percentile(errors, 95),
        "max_m": max(errors),
    }


def write_outputs(campaign_dir: Path, aligned: list[dict[str, object]], stats: dict[str, object]) -> None:
    analysis = campaign_dir / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)

    # Parquet if pandas available, else JSONL fallback.
    try:
        import pandas as pd

        pd.DataFrame(aligned).to_parquet(analysis / "aligned_epochs.parquet", index=False)
    except ImportError:
        with (analysis / "aligned_epochs.jsonl").open("w", encoding="utf-8") as f:
            for row in aligned:
                f.write(json.dumps(row) + "\n")

    (analysis / "summary_stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    try:
        import matplotlib.pyplot as plt

        errors = [float(r["e_h_m"]) for r in aligned]
        if errors:
            fig_dir = analysis / "figures"
            fig_dir.mkdir(exist_ok=True)
            plt.figure(figsize=(6, 4))
            plt.hist(errors, bins=40, color="#0d9488", edgecolor="white")
            plt.xlabel("Horizontal error (m)")
            plt.ylabel("Count")
            plt.title("AIS vs onboard GNSS — horizontal error")
            plt.tight_layout()
            plt.savefig(fig_dir / "error_hist.png", dpi=150)
            plt.close()
    except ImportError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2 field campaign AIS vs GNSS analysis")
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--mmsi", type=int, help="Recorded in summary only")
    parser.add_argument("--max-pair-delta-s", type=float, default=5.0)
    args = parser.parse_args()

    campaign = args.campaign_dir
    gnss_path = campaign / "gnss" / "ppk_solution.csv"
    ais_path = campaign / "ais" / "barentswatch_track.json"

    if not gnss_path.is_file():
        raise SystemExit(f"Missing {gnss_path} — run PPK and export ppk_solution.csv first")
    if not ais_path.is_file():
        raise SystemExit(f"Missing {ais_path} — export BarentsWatch track first")

    gnss = load_gnss_csv(gnss_path)
    ais = load_ais_barentswatch_json(ais_path)
    aligned = align_epochs(ais, gnss, max_pair_delta_s=args.max_pair_delta_s)
    errors = [float(r["e_h_m"]) for r in aligned]

    stats: dict[str, object] = {
        "mmsi": args.mmsi,
        "campaign_dir": str(campaign.resolve()),
        "gnss_epochs": len(gnss),
        "ais_epochs": len(ais),
        "aligned_pairs": len(aligned),
        "horizontal_error_m": summarise_errors(errors),
        "notes": "Skeleton output — review fix_type filters and interpolation before publication",
    }

    write_outputs(campaign, aligned, stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
