from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from aistruth_core.ais_adapter import AisPositionReport
from aistruth_core.track_heuristics import implied_speed_knots


@dataclass(frozen=True)
class SpoofingFinding:
    kind: str
    severity: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def impossible_jump_detector(
    reports: list[AisPositionReport],
    *,
    high_speed_knots: float = 45.0,
    implausible_speed_knots: float = 60.0,
) -> list[SpoofingFinding]:
    ordered = sorted(reports, key=lambda report: report.t)
    findings: list[SpoofingFinding] = []
    for prev, cur in zip(ordered, ordered[1:], strict=False):
        speed = implied_speed_knots(prev, cur)
        if speed is None:
            findings.append(
                SpoofingFinding(
                    kind="non_monotonic_or_zero_dt",
                    severity="medium",
                    evidence={"from": prev.t.isoformat(), "to": cur.t.isoformat()},
                )
            )
            continue
        if speed > implausible_speed_knots:
            severity = "high"
            kind = "implausible_speed_over_60kt"
        elif speed > high_speed_knots:
            severity = "medium"
            kind = "high_speed_over_45kt"
        else:
            continue
        findings.append(
            SpoofingFinding(
                kind=kind,
                severity=severity,
                evidence={
                    "from": prev.t.isoformat(),
                    "to": cur.t.isoformat(),
                    "implied_speed_knots": speed,
                },
            )
        )
    return _dedupe_findings(findings)


def position_freeze_detector(
    reports: list[AisPositionReport],
    *,
    min_repeated_points: int = 3,
) -> list[SpoofingFinding]:
    ordered = sorted(reports, key=lambda report: report.t)
    if len(ordered) < min_repeated_points:
        return []
    findings: list[SpoofingFinding] = []
    streak_start = 0
    for idx in range(1, len(ordered)):
        prev = ordered[idx - 1]
        cur = ordered[idx]
        if cur.lat == prev.lat and cur.lon == prev.lon:
            continue
        if idx - streak_start >= min_repeated_points:
            findings.append(_freeze_finding(ordered[streak_start:idx]))
        streak_start = idx
    if len(ordered) - streak_start >= min_repeated_points:
        findings.append(_freeze_finding(ordered[streak_start:]))
    return findings


def mmsi_swap_detector(reports: list[AisPositionReport]) -> list[SpoofingFinding]:
    by_position: dict[tuple[float, float], set[int]] = {}
    for report in reports:
        by_position.setdefault((report.lat, report.lon), set()).add(report.mmsi)
    return [
        SpoofingFinding(
            kind="mmsi_swap_same_position",
            severity="medium",
            evidence={"lat": lat, "lon": lon, "mmsi": sorted(mmsi_values)},
        )
        for (lat, lon), mmsi_values in by_position.items()
        if len(mmsi_values) > 1
    ]


def gnss_jamming_correlator_v0() -> list[SpoofingFinding]:
    return [
        SpoofingFinding(
            kind="gnss_jamming_context_unavailable",
            severity="info",
            evidence={"reason": "GEODNET ionospheric or jamming context not integrated yet"},
        )
    ]


def analyze_spoofing(reports: list[AisPositionReport]) -> list[SpoofingFinding]:
    findings: list[SpoofingFinding] = []
    findings.extend(impossible_jump_detector(reports))
    findings.extend(position_freeze_detector(reports))
    return _dedupe_findings(findings)


def _freeze_finding(streak: list[AisPositionReport]) -> SpoofingFinding:
    first = streak[0]
    last = streak[-1]
    return SpoofingFinding(
        kind="position_freeze",
        severity="medium",
        evidence={
            "lat": first.lat,
            "lon": first.lon,
            "count": len(streak),
            "from": first.t.isoformat(),
            "to": last.t.isoformat(),
        },
    )


def _dedupe_findings(findings: list[SpoofingFinding]) -> list[SpoofingFinding]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SpoofingFinding] = []
    for finding in findings:
        key = (finding.kind, str(sorted(finding.evidence.items())))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped
