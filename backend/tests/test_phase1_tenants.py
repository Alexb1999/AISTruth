from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations.ais_resolver import fetch_ais_reports
from aistruth_api.main import create_app
from aistruth_api.tenants import TenantRecord, create_tenant_with_key, hash_api_key, lookup_auth_by_raw_key


def test_hash_api_key_is_stable() -> None:
    assert hash_api_key("abc") == hash_api_key("abc")
    assert hash_api_key("abc") != hash_api_key("abcd")


@pytest.mark.asyncio
async def test_file_replay_ais_resolver() -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_track.jsonl"
    settings = Settings.model_construct(
        ais_source="file",
        file_replay_path=str(fixture),
        barentswatch_client_id=None,
        barentswatch_client_secret=None,
    )
    result = await fetch_ais_reports(mmsi=257000000, settings=settings, tenant=None)
    assert result.source.startswith("file_replay:")
    assert len(result.reports) == 2
    assert result.reports[0].lat == pytest.approx(44.6488)


@pytest.mark.asyncio
async def test_tenant_overrides_ais_source(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "sample_track.jsonl"
    tenant = TenantRecord(
        id=uuid4(),
        name="Demo",
        slug="demo",
        ais_source="file",
        spire_api_key=None,
        file_replay_path=str(fixture),
        pilot_ends_at=None,
    )
    settings = Settings.model_construct(
        ais_source="barentswatch",
        barentswatch_client_id=None,
        barentswatch_client_secret=None,
    )
    result = await fetch_ais_reports(mmsi=257000000, settings=settings, tenant=tenant)
    assert len(result.reports) == 2


@pytest.mark.asyncio
async def test_me_without_tenant_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AISTRUTH_API_KEYS", raising=False)
    get_settings.cache_clear()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/v1/me")
    get_settings.cache_clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant"] is None


@pytest.mark.asyncio
async def test_admin_usage_requires_admin_key() -> None:
    get_settings.cache_clear()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/v1/admin/usage")
        assert response.status_code == 503

        def settings_with_admin() -> Settings:
            return Settings.model_construct(admin_key="admin-secret")

        app.dependency_overrides[get_settings] = settings_with_admin
        missing = await client.get("/v1/admin/usage")
        assert missing.status_code == 401
        ok = await client.get("/v1/admin/usage", headers={"X-Admin-Key": "admin-secret"})
        assert ok.status_code == 200
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_tenant_db_auth_and_me() -> None:
    pytest.importorskip("asyncpg")
    database_url = Settings().database_url
    if not database_url:
        pytest.skip("DATABASE_URL not set")
    import asyncpg

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
    slug = f"test-{uuid4().hex[:8]}"
    async with pool.acquire() as conn, conn.transaction():
        tenant, raw_key = await create_tenant_with_key(
            conn,
            name="Test Tenant",
            slug=slug,
            ais_source="file",
            file_replay_path=str(Path(__file__).parent / "fixtures" / "sample_track.jsonl"),
        )
        auth = await lookup_auth_by_raw_key(conn, raw_key)
        assert auth is not None
        assert auth.tenant.slug == slug
    await pool.close()

    get_settings.cache_clear()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        me = await client.get("/v1/me", headers={"X-AIS-Key": raw_key})
        assert me.status_code == 200
        assert me.json()["tenant"]["slug"] == slug
        validate = await client.get(f"/v1/validate/{257000000}", headers={"X-AIS-Key": raw_key})
        assert validate.status_code == 200
    get_settings.cache_clear()
