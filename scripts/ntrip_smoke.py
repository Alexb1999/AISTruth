#!/usr/bin/env python3
"""Minimal NTRIP client smoke test for GEODNET RTK (or compatible caster).

Uses shared probe logic from ``aistruth_core``.

Usage:
  export GEODNET_NTRIP_USER=...
  export GEODNET_NTRIP_PASSWORD=...
  python scripts/ntrip_smoke.py --seconds 20

Or load a local env file (does not override variables already set in your shell):

  python scripts/ntrip_smoke.py --env-file apps/api/.env --seconds 20

Optional env:
  GEODNET_NTRIP_HOST (default rtk.geodnet.com)
  GEODNET_NTRIP_PORT (default 2101)
  GEODNET_NTRIP_MOUNT (default AUTO)
  GEODNET_SMOKE_LAT  (default 59.6667  Oslofjord entrance)
  GEODNET_SMOKE_LON  (default 10.6333)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path


def load_env_file(path: str) -> None:
    """Load KEY=VALUE pairs into the process environment (no override if key exists)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if key not in os.environ:
            os.environ[key] = value


try:
    from aistruth_core.nmea_gga import build_gpgga
    from aistruth_core.ntrip_probe import run_ntrip_probe
except ImportError:  # pragma: no cover - convenience when running without editable install
    _root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(_root / "packages" / "core"))
    from aistruth_core.nmea_gga import build_gpgga
    from aistruth_core.ntrip_probe import run_ntrip_probe


async def _async_main(*, seconds: float) -> int:
    user = os.environ.get("GEODNET_NTRIP_USER")
    password = os.environ.get("GEODNET_NTRIP_PASSWORD")
    if not user or not password:
        print(
            "Set GEODNET_NTRIP_USER and GEODNET_NTRIP_PASSWORD (trial credentials from GEODNET).",
            file=sys.stderr,
        )
        return 2

    host = os.environ.get("GEODNET_NTRIP_HOST") or "rtk.geodnet.com"
    port = int(os.environ.get("GEODNET_NTRIP_PORT") or "2101")
    mount = os.environ.get("GEODNET_NTRIP_MOUNT") or "AUTO"
    lat = float(os.environ.get("GEODNET_SMOKE_LAT", "59.6667"))
    lon = float(os.environ.get("GEODNET_SMOKE_LON", "10.6333"))

    def gga_factory() -> bytes:
        t = time.gmtime()
        hhmmss = f"{t.tm_hour:02d}{t.tm_min:02d}{t.tm_sec:02d}.00"
        return build_gpgga(lat, lon, utc_hhmmss=hhmmss)

    print(f"Connecting NTRIP {host}:{port} mount=/{mount} GGA@{lat:.6f},{lon:.6f} ...")
    res = await run_ntrip_probe(
        host=host,
        port=port,
        mount=mount,
        user=user,
        password=password,
        gga_factory=gga_factory,
        seconds=seconds,
        gga_lat=lat,
        gga_lon=lon,
    )
    print("--- NTRIP response (first header line) ---")
    print(res.first_header_line)
    print("--- Summary ---")
    print(f"ok={res.ok} bytes_total={res.bytes_total} tcp_chunks={res.tcp_chunks}")
    print(
        f"rtcm_frame_count={res.rtcm_frame_count} "
        f"rtcm_invalid_frame_count={res.rtcm_invalid_frame_count} "
        f"rtcm_message_counts={res.rtcm_message_counts}"
    )
    if res.error:
        print(f"error={res.error}", file=sys.stderr)
    return 0 if res.ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="NTRIP smoke test for GEODNET RTK")
    parser.add_argument(
        "--seconds",
        type=float,
        default=15.0,
        help="How long to read after connect",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Optional dotenv-style file (KEY=VALUE) to populate missing env vars",
    )
    args = parser.parse_args()

    if args.env_file:
        try:
            load_env_file(args.env_file)
        except OSError as e:
            print(f"Could not read env file: {e}", file=sys.stderr)
            return 2

    try:
        return asyncio.run(_async_main(seconds=args.seconds))
    except TimeoutError as e:
        print(f"Timeout: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
