from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from aistruth_core.adapters.file_replay import FileReplayAisSource


@pytest.mark.asyncio
async def test_file_replay_source_yields_reports(tmp_path: Path) -> None:
    fixture = tmp_path / "track.jsonl"
    fixture.write_text(
        '{"mmsi":257000000,"time":"2026-01-01T00:00:00Z","lat":60.0,"lon":5.0}\n',
        encoding="utf-8",
    )

    reports = [report async for report in FileReplayAisSource(fixture)]

    assert len(reports) == 1
    assert reports[0].mmsi == 257000000
    assert reports[0].t == datetime(2026, 1, 1, tzinfo=UTC)
    assert reports[0].lat == 60.0
    assert reports[0].lon == 5.0
