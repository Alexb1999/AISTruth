from __future__ import annotations

import httpx
import pytest

from aistruth_api.integrations.barentswatch_client import format_upstream_http_error


def test_format_oauth_error_includes_setup_hint() -> None:
    req = httpx.Request("POST", "https://id.barentswatch.no/connect/token")
    resp = httpx.Response(401, request=req, text='{"error":"invalid_client"}')
    exc = httpx.HTTPStatusError("401", request=req, response=resp)
    msg = format_upstream_http_error(exc)
    assert "OAuth token request failed" in msg
    assert "BARENTSWATCH_CLIENT_ID" in msg
    assert "invalid_client" in msg


def test_format_live_ais_401() -> None:
    req = httpx.Request("GET", "https://live.ais.barentswatch.no/v1/latest/combined")
    resp = httpx.Response(401, request=req)
    exc = httpx.HTTPStatusError("401", request=req, response=resp)
    msg = format_upstream_http_error(exc)
    assert "live AIS returned HTTP 401" in msg


@pytest.mark.parametrize(
    ("host", "substring"),
    [
        (
            "https://historic.ais.barentswatch.no/v1/historic/trackslast24hours/123",
            "historic AIS returned HTTP 401",
        ),
    ],
)
def test_format_historic_401(host: str, substring: str) -> None:
    req = httpx.Request("GET", host)
    resp = httpx.Response(401, request=req)
    exc = httpx.HTTPStatusError("401", request=req, response=resp)
    assert substring in format_upstream_http_error(exc)
