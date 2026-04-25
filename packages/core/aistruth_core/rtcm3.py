"""Lightweight RTCM3 helpers with CRC24Q frame validation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass

CRC24Q_POLY = 0x1864CFB


@dataclass(frozen=True)
class Rtcm3Frame:
    message_number: int | None
    payload: bytes
    payload_length: int


def crc24q(data: bytes | bytearray | memoryview) -> int:
    """Return RTCM3 CRC24Q over ``data``."""
    crc = 0
    for byte in bytes(data):
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= CRC24Q_POLY
            crc &= 0xFFFFFF
    return crc


def iter_rtcm3_frames(buf: bytes | bytearray | memoryview) -> Iterator[tuple[int | None, int]]:
    """Yield ``(message_number_or_none, payload_len)`` for each CRC-valid RTCM3 frame."""
    for frame in iter_rtcm3_frame_payloads(buf):
        yield frame.message_number, frame.payload_length


def iter_rtcm3_frame_payloads(buf: bytes | bytearray | memoryview) -> Iterator[Rtcm3Frame]:
    """Yield CRC-valid RTCM3 frames with payload bytes."""
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
        frame = mv[i : i + frame_len]
        expected_crc = int.from_bytes(frame[-3:], "big")
        if crc24q(frame[:-3]) != expected_crc:
            i += 1
            continue
        payload = mv[i + 3 : i + 3 + length]
        msg_no: int | None = None
        if len(payload) >= 2:
            msg_no = ((payload[0] << 4) | (payload[1] >> 4)) & 0x0FFF
        yield Rtcm3Frame(
            message_number=msg_no,
            payload=payload.tobytes(),
            payload_length=int(length),
        )
        i += frame_len


def summarize_rtcm3_stream(buf: bytes | bytearray) -> tuple[int, int, dict[int, int]]:
    """Return ``(valid_frame_count, invalid_frame_count, {message_number: count})``."""
    mv = memoryview(buf)
    counts: dict[int, int] = defaultdict(int)
    valid_frames = 0
    invalid_frames = 0
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
        frame = mv[i : i + frame_len]
        expected_crc = int.from_bytes(frame[-3:], "big")
        if crc24q(frame[:-3]) != expected_crc:
            invalid_frames += 1
            i += 1
            continue
        payload = mv[i + 3 : i + 3 + length]
        msg_no: int | None = None
        if len(payload) >= 2:
            msg_no = ((payload[0] << 4) | (payload[1] >> 4)) & 0x0FFF
        valid_frames += 1
        key = msg_no if msg_no is not None else -1
        counts[key] += 1
        i += frame_len
    return valid_frames, invalid_frames, dict(counts)
