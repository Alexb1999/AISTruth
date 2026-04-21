"""Pluggable AIS sources (Gap 3 / Phase 1).

Concrete adapters (file replay, AISHub, Norwegian open data, Spire BYOK) implement
:class:`AisSource` and yield :class:`AisPositionReport` for the fusion pipeline.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AisPositionReport:
    """Minimal decoded AIS position for ingestion."""

    mmsi: int
    t: datetime
    lat: float
    lon: float


@runtime_checkable
class AisSource(Protocol):
    """Async stream of position reports from any upstream."""

    def __aiter__(self) -> AsyncIterator[AisPositionReport]: ...
