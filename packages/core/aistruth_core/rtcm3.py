"""Lightweight RTCM3 helpers (frame scan + message number extraction, no CRC verify)."""

from __future__ import annotations

from collections import defaultdict


def iter_rtcm3_frames(buf: bytes | bytearray | memoryview):
    """Yield ``(message_number_or_none, payload_len)`` for each plausible RTCM3 frame.

    CRC is **not** validated; malformed streams may produce false positives. Good enough
    for telemetry and coarse health checks on live caster bytes.
    """
    mv = memoryview(buf)
    i = 0
    lim = len(mv)
    while i + 6 <= lim:
        if mv[i] != 0xD3:
            i += 1
            continue
        length = int(((mv[i + 1] & 0x03) << 8) | mv[i + 2])
        frame_len = 3 + length + 3
        if i + frame_len > lim:
            break
        payload = mv[i + 3 : i + 3 + length]
        msg_no: int | None = None
        if len(payload) >= 2:
            msg_no = ((payload[0] << 4) | (payload[1] >> 4)) & 0x0FFF
        yield msg_no, int(length)
        i += frame_len


def summarize_rtcm3_stream(buf: bytes | bytearray) -> tuple[int, dict[int, int]]:
    """Return ``(frame_count, {message_number: count})``."""
    counts: dict[int, int] = defaultdict(int)
    frames = 0
    for msg_no, _length in iter_rtcm3_frames(buf):
        frames += 1
        key = msg_no if msg_no is not None else -1
        counts[key] += 1
    return frames, dict(counts)
