# ADR 002: RTK fusion library path

## Status

Accepted for MVP contract; revisit before production RTK solving.

## Context

AISTruth can consume GEODNET NTRIP/RTCM correction streams, but AIS reports are not rover GNSS observations. A true centimeter-class RTK solution requires rover-side GNSS measurements, correction data, ephemeris, and a solver.

## Decision

- Keep `aistruth_core.fusion.RtkFusionEngine` as the stable API contract for fusion evidence.
- Use `gnss-lib-py` as the preferred first solver candidate when rover observations are available because it is Python-native and easier to integrate into the current FastAPI/core stack.
- Keep RTKLIB bindings or `rnx2rtkp` as a later performance/accuracy spike if `gnss-lib-py` cannot meet production needs.
- Until rover observations exist, return `status: telemetry_only_rover_observations_unavailable` and do not claim a centimeter-class refined position.

## Consequences

- `/v1/validate/{mmsi}?fusion=true` can be integrated by clients now without overclaiming.
- The evidence bundle can grow from telemetry-backed to true solver-backed output without changing the top-level API shape.
- Future work must add rover observation ingest before marking RTK refinement as production-ready.
