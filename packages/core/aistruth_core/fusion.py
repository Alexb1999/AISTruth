from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class RtkFusionResult:
    ok: bool
    method: str
    refined_lat: float | None
    refined_lon: float | None
    baseline_m: float | None
    correction_age_s: float | None
    pdop: float | None
    status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class RtkFusionEngine:
    """RTK fusion contract for `/v1/validate?fusion=true`.

    The current engine can verify correction-stream freshness and return an evidence bundle,
    but cannot compute a centimeter-class rover solution until real rover GNSS observations
    are available alongside AIS.
    """

    method = "rtk_v1"

    def build_result(
        self,
        *,
        latest_ais_lat: float,
        latest_ais_lon: float,
        baseline_m: float | None,
        correction_received_at: datetime | None,
    ) -> RtkFusionResult:
        correction_age_s = None
        if correction_received_at is not None:
            correction_age_s = max(
                0.0,
                (datetime.now(UTC) - correction_received_at).total_seconds(),
            )
        return RtkFusionResult(
            ok=correction_received_at is not None,
            method=self.method,
            refined_lat=latest_ais_lat if correction_received_at is not None else None,
            refined_lon=latest_ais_lon if correction_received_at is not None else None,
            baseline_m=baseline_m,
            correction_age_s=correction_age_s,
            pdop=None,
            status="telemetry_only_rover_observations_unavailable",
        )
