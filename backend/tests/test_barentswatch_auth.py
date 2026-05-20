from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations import barentswatch_client
from aistruth_api.main import create_app


@pytest.mark.asyncio
async def test_norway_vessels_requires_key_when_barentswatch_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "test-secret")
    monkeypatch.delenv("AISTRUTH_API_KEYS", raising=False)
    get_settings.cache_clear()
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/v1/ais/norway/vessels?limit=5")

    get_settings.cache_clear()
    assert response.status_code == 401
    assert "X-AIS-Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_norway_vessels_allows_env_key(
    app: FastAPI,
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AISTRUTH_API_KEYS", "operator-key")
    monkeypatch.setenv("AISTRUTH_AIS_SOURCE", "barentswatch")
    get_settings.cache_clear()

    async def fake_token(cid: str, sec: str) -> str:
        return "t"

    async def fake_all(token: str, *, ttl_seconds: int) -> list[dict[str, Any]]:
        return [
            {
                "mmsi": 259139000,
                "latitude": 63.0,
                "longitude": 9.5,
                "msgtime": "2026-01-01T12:00:00+00:00",
                "name": "NORDLYS",
            }
        ]

    monkeypatch.setattr(barentswatch_client, "fetch_access_token", fake_token)
    monkeypatch.setattr(barentswatch_client, "fetch_latest_all_combined_cached", fake_all)

    response = await client.get(
        "/v1/ais/norway/vessels?limit=5",
        headers={"X-AIS-Key": "operator-key"},
    )
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()[0]["mmsi"] == 259139000


@pytest.mark.asyncio
async def test_validate_barentswatch_requires_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AISTRUTH_AIS_SOURCE", "barentswatch")
    monkeypatch.delenv("AISTRUTH_API_KEYS", raising=False)
    get_settings.cache_clear()
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/v1/validate/257111020")

    get_settings.cache_clear()
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_validate_file_replay_does_not_require_barentswatch_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "sample_track.jsonl"
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("AISTRUTH_AIS_SOURCE", "file")
    monkeypatch.setenv("FILE_REPLAY_PATH", str(fixture))
    monkeypatch.delenv("AISTRUTH_API_KEYS", raising=False)
    get_settings.cache_clear()
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/v1/validate/257000000")

    get_settings.cache_clear()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_norway_vessels_rejects_file_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pathlib import Path
    from uuid import uuid4

    pytest.importorskip("asyncpg")
    database_url = Settings().database_url
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    import asyncpg

    from aistruth_api.tenants import create_tenant_with_key

    fixture = Path(__file__).parent / "fixtures" / "sample_track.jsonl"
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "test-secret")
    get_settings.cache_clear()

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    slug = f"file-{uuid4().hex[:8]}"
    async with pool.acquire() as conn, conn.transaction():
        _, raw_key = await create_tenant_with_key(
            conn,
            name="File Tenant",
            slug=slug,
            ais_source="file",
            file_replay_path=str(fixture),
        )
    await pool.close()

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get(
            "/v1/ais/norway/vessels?limit=5",
            headers={"X-AIS-Key": raw_key},
        )

    get_settings.cache_clear()
    assert response.status_code == 403
    assert "barentswatch" in response.json()["detail"].lower()
