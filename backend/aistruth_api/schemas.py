from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class TimeAlignResult(BaseModel):
    lat: float
    lon: float
    method: str


class QueryPoint(BaseModel):
    lat: float
    lon: float


class NearestNodeResponse(BaseModel):
    id: str
    name: str
    distance_m: float
    query: QueryPoint


class GeodnetSyncResponse(BaseModel):
    """Result of ``POST /v1/geodnet/sync-stations``."""

    upserted: int


class NorwayPoint(BaseModel):
    mmsi: int
    time: str
    lat: float
    lon: float


class NorwayVesselSnippet(BaseModel):
    """One vessel from GET ``/v1/latest/combined`` (for picking an MMSI without MarineTraffic)."""

    mmsi: int
    lat: float
    lon: float
    time: str
    name: str | None = None


class ValidateWindow(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = {"populate_by_name": True}


class NtripProbeSummary(BaseModel):
    ok: bool
    host: str | None = None
    port: int | None = None
    mount: str | None = None
    seconds: float | None = None
    duration_s: float | None = None
    gga_lat: float | None = None
    gga_lon: float | None = None
    http_status: str | None = None
    first_header_line: str | None = None
    bytes_total: int | None = None
    tcp_chunks: int | None = None
    rtcm_frame_count: int | None = None
    rtcm_invalid_frame_count: int | None = None
    rtcm_message_counts: dict[int, int] | None = None
    error: str | None = None


class SpoofingFindingSchema(BaseModel):
    kind: str
    severity: str
    evidence: dict[str, Any]


class FusionResultSchema(BaseModel):
    ok: bool
    method: str
    refined_lat: float | None = None
    refined_lon: float | None = None
    baseline_m: float | None = None
    correction_age_s: float | None = None
    pdop: float | None = None
    status: str


class MapTrackPoint(BaseModel):
    """Time-ordered AIS fix for dashboard map overlays (may be downsampled)."""

    lat: float
    lon: float
    time: str


class NearestNodeMapInfo(BaseModel):
    """Nearest GEODNET node used for baseline context, with map coordinates."""

    id: str
    name: str
    lat: float
    lon: float
    distance_m: float


class GeodnetCatalogInfo(BaseModel):
    """Station catalog honesty metadata for demos vs live GEODNET sync."""

    mode: str = Field(description="fixture | hybrid | synced")
    active_node_count: int = 0
    synced_node_count: int = 0
    fixture_node_count: int = 0
    last_synced_at: str | None = None
    demo_warning: bool = False


class GeodnetMapNode(BaseModel):
    """Reference station for map overlays (precision footprint visualization)."""

    id: str
    name: str
    lat: float
    lon: float
    distance_m: float | None = None
    is_nearest: bool = False


class ValidateEvidence(BaseModel):
    track_points: int
    source: str
    rules_version: str
    nearest_node_id: str | None = None
    baseline_m: float | None = None
    nearest_node: NearestNodeMapInfo | None = None
    map_track_points: list[MapTrackPoint] = Field(default_factory=list)
    geodnet_map_nodes: list[GeodnetMapNode] = Field(
        default_factory=list,
        description="K-nearest active GEODNET nodes to latest AIS (for map overlays).",
    )
    geodnet_catalog: GeodnetCatalogInfo | None = Field(
        default=None,
        description="Catalog mode and counts — surfaces demo vs synced network in UI.",
    )
    max_implied_speed_knots: float | None = None
    time_align_method: str
    spoofing_findings: list[SpoofingFindingSchema] = Field(default_factory=list)
    fusion_result: FusionResultSchema | None = None
    geodnet_ntrip_probe: NtripProbeSummary | dict[str, object] | None = None


class ValidateResponse(BaseModel):
    mmsi: int
    window: ValidateWindow
    confidence_score: int
    flags: list[str]
    evidence: ValidateEvidence


class BulkValidateRequest(BaseModel):
    mmsi: list[int] = Field(min_length=1, max_length=50)
    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None
    fusion: bool = False

    model_config = {"populate_by_name": True}


class BulkValidateResult(BaseModel):
    mmsi: int
    result: ValidateResponse | None = None
    error: str | None = None
    status_code: int | None = None


class BulkValidateResponse(BaseModel):
    results: list[BulkValidateResult]


class ValidationRunRecord(BaseModel):
    id: str
    mmsi: int
    requested_at: datetime
    window: ValidateWindow
    confidence_score: int
    flags: list[str]
    evidence: dict[str, Any]
