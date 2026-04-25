from aistruth_core.rtcm3 import crc24q, iter_rtcm3_frames, summarize_rtcm3_stream


def _make_rtcm3_frame(message_number: int, extra_payload: bytes = b"") -> bytes:
    """Synthetic RTCM3 frame with a valid CRC24Q."""
    b0 = (message_number >> 4) & 0xFF
    b1 = ((message_number & 0x0F) << 4) & 0xFF
    payload = bytes([b0, b1]) + extra_payload
    length = len(payload)
    assert length < 1024
    byte1 = (length >> 8) & 0x03
    byte2 = length & 0xFF
    frame_without_crc = bytes([0xD3, byte1, byte2]) + payload
    return frame_without_crc + crc24q(frame_without_crc).to_bytes(3, "big")


def test_summarize_two_frames() -> None:
    buf = _make_rtcm3_frame(1005) + _make_rtcm3_frame(1074) + _make_rtcm3_frame(1074)
    frames, invalid_frames, counts = summarize_rtcm3_stream(buf)
    assert frames == 3
    assert invalid_frames == 0
    assert counts[1005] == 1
    assert counts[1074] == 2


def test_iter_skips_garbage_between_frames() -> None:
    buf = b"\xff\xfe" + _make_rtcm3_frame(1005)
    frames = list(iter_rtcm3_frames(buf))
    assert len(frames) == 1
    assert frames[0][0] == 1005


def test_invalid_crc_is_rejected() -> None:
    valid = _make_rtcm3_frame(1077)
    invalid = valid[:-1] + bytes([valid[-1] ^ 0xFF])

    frames, invalid_frames, counts = summarize_rtcm3_stream(valid + invalid)

    assert frames == 1
    assert invalid_frames == 1
    assert counts == {1077: 1}
    assert list(iter_rtcm3_frames(invalid)) == []
