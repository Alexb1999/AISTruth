"""Async NTRIP client probe (GEODNET-compatible): collect RTCM for N seconds with periodic GGA."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import time
from collections.abc import Callable
from dataclasses import dataclass

from aistruth_core.rtcm3 import summarize_rtcm3_stream


@dataclass(frozen=True)
class NtripProbeResult:
    ok: bool
    host: str
    port: int
    mount: str
    duration_s: float
    first_header_line: str | None
    bytes_total: int
    tcp_chunks: int
    rtcm_frame_count: int
    rtcm_invalid_frame_count: int
    rtcm_message_counts: dict[str, int]
    gga_lat: float
    gga_lon: float
    error: str | None = None


@dataclass(frozen=True)
class _HeaderOutcome:
    """NTRIP HTTP status + headers until blank line."""

    headers_text: str | None
    first_line: str | None
    failure: str | None
    preview: str | None = None


def _fail_early(
    *,
    t0: float,
    host: str,
    port: int,
    mount: str,
    gga_lat: float,
    gga_lon: float,
    error: str,
    first_header_line: str | None = None,
) -> NtripProbeResult:
    return NtripProbeResult(
        ok=False,
        host=host,
        port=port,
        mount=mount,
        duration_s=time.perf_counter() - t0,
        first_header_line=first_header_line,
        bytes_total=0,
        tcp_chunks=0,
        rtcm_frame_count=0,
        rtcm_invalid_frame_count=0,
        rtcm_message_counts={},
        gga_lat=gga_lat,
        gga_lon=gga_lon,
        error=error,
    )


async def _read_ntrip_http_headers(
    reader: asyncio.StreamReader,
    *,
    overall_s: float = 60.0,
    per_line_s: float = 25.0,
    icy_lookahead_s: float = 3.0,
) -> _HeaderOutcome:
    """Read until blank line; bounded time for slow casters and firewall half-opens."""
    lines: list[str] = []
    t_start = time.monotonic()
    while True:
        elapsed = time.monotonic() - t_start
        if elapsed >= overall_s:
            preview = "\n".join(lines).strip()
            if len(preview) > 400:
                preview = preview[:400] + "…"
            return _HeaderOutcome(
                None,
                lines[0] if lines else None,
                f"ntrip_http_header_timeout ({overall_s:.0f}s, no blank line ending headers)",
                preview or None,
            )
        budget = overall_s - elapsed
        line_to = min(per_line_s, budget)
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=line_to)
        except TimeoutError:
            preview = "\n".join(lines).strip()
            if len(preview) > 400:
                preview = preview[:400] + "…"
            return _HeaderOutcome(
                None,
                lines[0] if lines else None,
                f"ntrip_header_line_stall ({per_line_s:.0f}s without a complete header line)",
                preview or None,
            )
        if not raw:
            preview = "\n".join(lines).strip()
            if len(preview) > 400:
                preview = preview[:400] + "…"
            return _HeaderOutcome(
                None,
                lines[0] if lines else None,
                "connection_closed_during_ntrip_headers",
                preview or None,
            )
        text = raw.decode(errors="replace").rstrip("\r\n")
        lines.append(text)
        if text == "":
            joined = "\n".join(lines)
            return _HeaderOutcome(joined, lines[0] if lines else None, None, None)

        # NTRIP: many casters go straight to binary RTCM after the first "ICY 200 OK" line.
        # Waiting for another readline() would block until a 0x0a appears inside RTCM (often 25s+).
        if len(lines) == 1 and _is_ntrip_source_ok_line(text):
            elapsed = time.monotonic() - t_start
            budget = overall_s - elapsed
            icy_to = min(icy_lookahead_s, budget)
            try:
                raw2 = await asyncio.wait_for(reader.readline(), timeout=icy_to)
            except TimeoutError:
                joined = "\n".join(lines)
                return _HeaderOutcome(joined, lines[0], None, None)
            if not raw2:
                preview = "\n".join(lines).strip()
                if len(preview) > 400:
                    preview = preview[:400] + "…"
                return _HeaderOutcome(
                    None,
                    lines[0] if lines else None,
                    "connection_closed_during_ntrip_headers",
                    preview or None,
                )
            text2 = raw2.decode(errors="replace").rstrip("\r\n")
            lines.append(text2)
            if text2 == "":
                joined = "\n".join(lines)
                return _HeaderOutcome(joined, lines[0], None, None)
            continue


def _format_header_failure(out: _HeaderOutcome) -> str:
    msg = out.failure or "ntrip_header_unknown"
    if out.preview:
        return f"{msg} | received: {out.preview!r}"
    return msg


def _is_ntrip_source_ok_line(line: str) -> bool:
    """True for successful NTRIP source mount responses (stream follows)."""
    u = line.strip().upper()
    return u.startswith("ICY 200") or (u.startswith("HTTP/") and " 200" in u)


async def run_ntrip_probe(
    *,
    host: str,
    port: int,
    mount: str,
    user: str,
    password: str,
    gga_factory: Callable[[], bytes],
    seconds: float,
    gga_lat: float,
    gga_lon: float,
) -> NtripProbeResult:
    token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    req = (
        f"GET /{mount} HTTP/1.0\r\n"
        "User-Agent: NTRIP AISTruthProbe/0.1\r\n"
        f"Authorization: Basic {token}\r\n"
        "\r\n"
    ).encode("ascii")

    t0 = time.perf_counter()
    # Casters sometimes take a long gap between HTTP 200 and first RTCM; allow longer
    # idle reads than the collection window itself.
    read_timeout = max(25.0, float(seconds) + 20.0)

    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=30.0)
    except TimeoutError:
        return _fail_early(
            t0=t0,
            host=host,
            port=port,
            mount=mount,
            gga_lat=gga_lat,
            gga_lon=gga_lon,
            error="tcp_connect_timeout (30s)",
        )
    except OSError as e:
        return _fail_early(
            t0=t0,
            host=host,
            port=port,
            mount=mount,
            gga_lat=gga_lat,
            gga_lon=gga_lon,
            error=str(e),
        )

    first_line: str | None = None
    total = 0
    chunks = 0
    buf = bytearray()
    stream_stalled_before_data = False

    try:
        writer.write(req)
        await writer.drain()

        h_out = await _read_ntrip_http_headers(reader)
        if h_out.failure is not None:
            return _fail_early(
                t0=t0,
                host=host,
                port=port,
                mount=mount,
                gga_lat=gga_lat,
                gga_lon=gga_lon,
                error=_format_header_failure(h_out),
                first_header_line=h_out.first_line,
            )

        first_line = h_out.first_line

        writer.write(gga_factory())
        await writer.drain()

        stop = asyncio.Event()

        async def gga_loop() -> None:
            while not stop.is_set():
                await asyncio.sleep(5.0)
                if stop.is_set():
                    break
                writer.write(gga_factory())
                await writer.drain()

        gga_task = asyncio.create_task(gga_loop())

        deadline = time.monotonic() + seconds
        try:
            while time.monotonic() < deadline:
                try:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=read_timeout)
                except TimeoutError:
                    if total == 0:
                        stream_stalled_before_data = True
                    break
                if not chunk:
                    break
                chunks += 1
                total += len(chunk)
                buf.extend(chunk)
                if len(buf) > 8_000_000:
                    del buf[:-2_000_000]
        finally:
            stop.set()
            gga_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await gga_task
    finally:
        writer.close()
        with contextlib.suppress(OSError, TimeoutError):
            await writer.wait_closed()

    frames, invalid_frames, counts = summarize_rtcm3_stream(buf)
    counts_out = {str(k): int(v) for k, v in counts.items()}
    dur = time.perf_counter() - t0
    ok = bool(first_line and ("200" in first_line)) and total > 0
    err: str | None = None
    if stream_stalled_before_data:
        ok = False
        err = (
            f"no_rtcm_within_{read_timeout:.0f}s_after_gga "
            "(caster idle, wrong mount/credentials, or network filtering)"
        )
    elif not ok:
        if not first_line or "200" not in first_line:
            err = "unexpected_ntrip_headers"
        elif total <= 0:
            err = "no_bytes_received"

    return NtripProbeResult(
        ok=ok,
        host=host,
        port=port,
        mount=mount,
        duration_s=dur,
        first_header_line=first_line,
        bytes_total=total,
        tcp_chunks=chunks,
        rtcm_frame_count=frames,
        rtcm_invalid_frame_count=invalid_frames,
        rtcm_message_counts=counts_out,
        gga_lat=gga_lat,
        gga_lon=gga_lon,
        error=err,
    )
