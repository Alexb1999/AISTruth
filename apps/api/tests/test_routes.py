from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aistruth_api.config import Settings, get_settings
from aistruth_api.main import create_app


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_demo_time_align(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/demo/time-align",
        json={
            "t0": datetime(2026, 1, 1, 0, 0, tzinfo=UTC).isoformat(),
            "lat0": 0,
            "lon0": 0,
            "t1": datetime(2026, 1, 1, 0, 10, tzinfo=UTC).isoformat(),
            "lat1": 10,
            "lon1": 10,
            "target_t": datetime(2026, 1, 1, 0, 5, tzinfo=UTC).isoformat(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "slerp_great_circle"
    assert payload["lat"] == pytest.approx(5.019000697861147)
    assert payload["lon"] == pytest.approx(4.961631226702507)


@pytest.mark.asyncio
async def test_validate_missing_creds_503(app: FastAPI, client: AsyncClient) -> None:
    def settings_without_barentswatch() -> Settings:
        return Settings(barentswatch_client_id=None, barentswatch_client_secret=None)

    app.dependency_overrides[get_settings] = settings_without_barentswatch
    response = await client.get("/v1/validate/257000000")

    assert response.status_code == 503
    assert "BarentsWatch is not configured" in response.json()["detail"]


@pytest.mark.asyncio
async def test_nearest_node_no_db_503(client: AsyncClient) -> None:
    response = await client.get("/v1/nearest-node", params={"lat": 44.65, "lon": -63.57})

    assert response.status_code == 503
    assert "DATABASE_URL not set" in response.json()["detail"]


def test_debug_geodnet_route_disabled(app: FastAPI) -> None:
    routes = {getattr(route, "path", "") for route in app.routes}

    assert "/v1/debug/geodnet-ntrip" not in routes


@pytest.mark.asyncio
async def test_v1_routes_require_api_key_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AISTRUTH_API_KEYS", "test-key")
    get_settings.cache_clear()
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        missing_key = await client.post("/v1/demo/time-align", json={})
        valid_key = await client.post(
            "/v1/demo/time-align",
            headers={"X-AIS-Key": "test-key"},
            json={},
        )

    assert missing_key.status_code == 401
    assert valid_key.status_code == 422
    get_settings.cache_clear()
