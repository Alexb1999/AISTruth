from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from aistruth_core.time_sync import PositionSample, interpolate_position_at

router = APIRouter(tags=["demo"])


class TimeAlignDemoBody(BaseModel):
    """Two AIS samples and a correction epoch between them."""

    t0: datetime = Field(description="UTC time of first sample")
    lat0: float
    lon0: float
    t1: datetime = Field(description="UTC time of second sample")
    lat1: float
    lon1: float
    target_t: datetime = Field(description="UTC correction epoch (must be between t0 and t1)")


@router.post("/demo/time-align")
async def demo_time_align(body: TimeAlignDemoBody) -> dict[str, float | str]:
    samples = [
        PositionSample(body.t0, body.lat0, body.lon0),
        PositionSample(body.t1, body.lat1, body.lon1),
    ]
    lat, lon, method = interpolate_position_at(samples, body.target_t)
    return {"lat": lat, "lon": lon, "method": method}
