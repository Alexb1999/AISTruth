import asyncio

import pytest

from aistruth_core.ntrip_probe import _is_ntrip_source_ok_line, _read_ntrip_http_headers


def test_is_ntrip_ok_line() -> None:
    assert _is_ntrip_source_ok_line("ICY 200 OK")
    assert _is_ntrip_source_ok_line("icy 200 ok")
    assert _is_ntrip_source_ok_line("HTTP/1.0 200 OK")
    assert _is_ntrip_source_ok_line("HTTP/1.1 200 OK")
    assert not _is_ntrip_source_ok_line("ICY 401 Unauthorized")
    assert not _is_ntrip_source_ok_line("")


@pytest.mark.asyncio
async def test_read_headers_icy_then_immediate_binary_no_further_lines() -> None:
    """Simulate caster that sends RTCM without another CRLF after ICY 200 OK."""
    reader = asyncio.StreamReader()
    reader.feed_data(b"ICY 200 OK\r\n")
    reader.feed_data(b"\xd3\x00\x00")  # RTCM-ish bytes, no newline
    # EOF before headers: readline can return a partial line; avoid that in this test.

    out = await _read_ntrip_http_headers(
        reader, overall_s=10.0, per_line_s=5.0, icy_lookahead_s=0.2
    )

    assert out.failure is None
    assert out.first_line == "ICY 200 OK"
    assert out.headers_text is not None
    reader.feed_eof()
    leftover = await reader.read()
    assert b"\xd3\x00\x00" in leftover


@pytest.mark.asyncio
async def test_read_headers_icy_blank_line() -> None:
    reader = asyncio.StreamReader()
    reader.feed_data(b"ICY 200 OK\r\n\r\n")
    reader.feed_eof()

    out = await _read_ntrip_http_headers(reader, overall_s=10.0, per_line_s=5.0)

    assert out.failure is None
    assert out.first_line == "ICY 200 OK"
