from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.barentswatch import parse_msgtime


class FileReplayAisSource:
    """Replay AIS position reports from JSONL fixtures for deterministic tests."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    async def __aiter__(self) -> AsyncIterator[AisPositionReport]:
        async for report in self.iter_all():
            yield report

    async def iter_all(self) -> AsyncIterator[AisPositionReport]:
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row: dict[str, Any] = json.loads(line)
            yield AisPositionReport(
                mmsi=int(row["mmsi"]),
                t=parse_msgtime(str(row["time"])),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
            )

    async def fetch_reports_for_mmsi(self, mmsi: int) -> list[AisPositionReport]:
        out: list[AisPositionReport] = []
        async for report in self.iter_all():
            if report.mmsi == mmsi:
                out.append(report)
        out.sort(key=lambda r: r.t)
        return out
