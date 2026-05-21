"""Tests for Stage 2 field campaign analysis skeleton."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_analyze_field_campaign_skeleton(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures"
    campaign = tmp_path / "campaign"
    (campaign / "gnss").mkdir(parents=True)
    (campaign / "ais").mkdir(parents=True)
    shutil.copy(fixture_dir / "campaign_gnss_sample.csv", campaign / "gnss" / "ppk_solution.csv")
    shutil.copy(fixture_dir / "campaign_ais_sample.json", campaign / "ais" / "barentswatch_track.json")

    from scripts.analyze_field_campaign import align_epochs, load_ais_barentswatch_json, load_gnss_csv

    gnss = load_gnss_csv(campaign / "gnss" / "ppk_solution.csv")
    ais = load_ais_barentswatch_json(campaign / "ais" / "barentswatch_track.json")
    aligned = align_epochs(ais, gnss, max_pair_delta_s=5.0)

    assert len(aligned) == 2
    assert all(float(row["e_h_m"]) < 50 for row in aligned)


def test_analyze_field_campaign_cli(tmp_path: Path) -> None:
    fixture_dir = Path(__file__).parent / "fixtures"
    campaign = tmp_path / "campaign"
    (campaign / "gnss").mkdir(parents=True)
    (campaign / "ais").mkdir(parents=True)
    shutil.copy(fixture_dir / "campaign_gnss_sample.csv", campaign / "gnss" / "ppk_solution.csv")
    shutil.copy(fixture_dir / "campaign_ais_sample.json", campaign / "ais" / "barentswatch_track.json")

    backend = Path(__file__).resolve().parents[1]
    script = backend / "scripts" / "analyze_field_campaign.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--campaign-dir",
            str(campaign),
            "--mmsi",
            "259123456",
        ],
        cwd=backend,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr

    summary_path = campaign / "analysis" / "summary_stats.json"
    assert summary_path.is_file()
    stats = json.loads(summary_path.read_text(encoding="utf-8"))
    assert stats["aligned_pairs"] == 2
