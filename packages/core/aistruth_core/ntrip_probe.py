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
    rtcm_message_counts: dict[str, int]
    gga_lat: float
    gga_lon: float
    error: str | None = None


async def _read_headers(reader: asyncio.StreamReader) -> str:
    lines: list[str] = []
    while True:
        line = await reader.readline()
        if not line:
            raise RuntimeError("Connection closed while reading headers")
        text = line.decode(errors="replace").rstrip("\r\n")
        lines.append(text)
        if text == "":
            break
    return "\n".join(lines)


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
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=30.0)
    except OSError as e:
        return NtripProbeResult(
            ok=False,
            host=host,
            port=port,
            mount=mount,
            duration_s=time.perf_counter() - t0,
            first_header_line=None,
            bytes_total=0,
            tcp_chunks=0,
            rtcm_frame_count=0,
            rtcm_message_counts={},
            gga_lat=gga_lat,
            gga_lon=gga_lon,
            error=str(e),
        )

    first_line: str | None = None
    total = 0
    chunks = 0
    buf = bytearray()
    try:
        writer.write(req)
        await writer.drain()

        headers = await asyncio.wait_for(_read_headers(reader), timeout=30.0)
        first_line = headers.splitlines()[0] if headers else None

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
                chunk = await asyncio.wait_for(reader.read(4096), timeout=10.0)
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
        with contextlib.suppress(Exception):
            await writer.wait_closed()

    frames, counts = summarize_rtcm3_stream(buf)
    counts_out = {str(k): int(v) for k, v in counts.items()}
    dur = time.perf_counter() - t0
    ok = bool(first_line and ("200" in first_line)) and total > 0
    err: str | None = None
    if not ok:
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
        rtcm_message_counts=counts_out,
        gga_lat=gga_lat,
        gga_lon=gga_lon,
        error=err,
    )
