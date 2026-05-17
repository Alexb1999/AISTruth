from __future__ import annotations

import json

import pytest

from aistruth_core.geodnet_rtk import (
    GeodnetStation,
    build_geodnet_sign,
    parse_station_list_response,
    station_list_request_body,
)


def test_build_geodnet_sign_matches_official_create_account_example() -> None:
    """Vector from GEODNET_RTK_API.md (Create account)."""
    app_key = "2916350764adb542"
    params = {
        "appId": "geodnet",
        "username": "geoduser",
        "password": "geodpass",
        "trialDays": 7,
        "time": 1718150400000,
    }
    assert build_geodnet_sign(params, app_key) == "8dd687e158219da6ccc689aef6c0a6a1"


def test_station_list_request_sign_matches_create_random_account_example() -> None:
    """Same sign algorithm as ``Create random account`` (appId + time only)."""
    app_key = "2916350764adb542"
    body = station_list_request_body(
        app_id="geodnet",
        app_key=app_key,
        time_ms=1718150400000,
    )
    assert body["sign"] == "f4c91395df1b944762293987f4c1fbab"


def test_station_list_request_body_includes_optional_region() -> None:
    app_key = "secret"
    body = station_list_request_body(
        app_id="a",
        app_key=app_key,
        time_ms=100,
        region="NOR",
    )
    assert body["region"] == "NOR"
    assert body["appId"] == "a"
    assert body["time"] == 100
    assert "sign" in body


def test_parse_station_list_ok() -> None:
    payload = {
        "code": 1000,
        "msg": "OK",
        "data": [
            {
                "name": "STN1",
                "latitude": 38.95,
                "longitude": -8.15,
                "height": 140.41,
                "status": "ACTIVE",
            }
        ],
    }
    stations = parse_station_list_response(payload)
    assert len(stations) == 1
    s = stations[0]
    assert s == GeodnetStation(
        name="STN1",
        latitude=38.95,
        longitude=-8.15,
        height_m=140.41,
        status="ACTIVE",
    )
    assert s.node_id == "geodnet:STN1"
    assert s.is_active_for_ingest is True


def test_parse_station_list_api_error_raises() -> None:
    with pytest.raises(ValueError, match="code=1003"):
        parse_station_list_response({"code": 1003, "msg": "sign error"})


def test_station_list_response_from_json_string() -> None:
    text = json.dumps(
        {
            "code": 1000,
            "msg": "OK",
            "data": [
                {"name": "X", "latitude": 1, "longitude": 2, "status": "OFFLINE"},
            ],
        }
    )
    stations = parse_station_list_response(json.loads(text))
    assert len(stations) == 1
    assert stations[0].is_active_for_ingest is False
