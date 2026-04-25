from __future__ import annotations

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


class NorwayPoint(BaseModel):
    mmsi: int
    time: str
    lat: float
    lon: float


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
    gga_lat: float | None = None
    gga_lon: float | None = None
    http_status: str | None = None
    bytes_total: int | None = None
    rtcm_frame_count: int | None = None
    rtcm_message_counts: dict[int, int] | None = None
    error: str | None = None


class ValidateEvidence(BaseModel):
    track_points: int
    source: str
    rules_version: str
    nearest_node_id: str | None = None
    baseline_m: float | None = None
    max_implied_speed_knots: float | None = None
    time_align_method: str
    geodnet_ntrip_probe: NtripProbeSummary | dict[str, object] | None = None


class ValidateResponse(BaseModel):
    mmsi: int
    window: ValidateWindow
    confidence_score: int
    flags: list[str]
    evidence: ValidateEvidence
