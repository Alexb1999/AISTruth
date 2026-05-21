from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aistruth_api.config import Settings, get_settings
from aistruth_api.main import create_app

LEAD_BODY = {
    "name": "Alex Test",
    "organization": "Test Shipping",
    "email": "alex@example.com",
    "region": "Norwegian coastal waters",
    "fleet_size": "6–25 vessels",
    "ais_feed": "BarentsWatch / Norway open AIS",
}


def _settings_leads_enabled(*, key: str | None = None) -> Settings:
    return Settings.model_construct(
        leads_enabled=True,
        leads_key=key,
        database_url=None,
    )


@pytest.mark.asyncio
async def test_create_lead_disabled_by_default_404(client: AsyncClient) -> None:
    response = await client.post("/v1/leads", json=LEAD_BODY)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_lead_requires_key_when_configured(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings_leads_enabled(key="secret-leads-key")

    missing = await client.post("/v1/leads", json=LEAD_BODY)
    wrong = await client.post(
        "/v1/leads",
        json=LEAD_BODY,
        headers={"X-Leads-Key": "wrong"},
    )

    app.dependency_overrides.clear()
    assert missing.status_code == 401
    assert wrong.status_code == 401


@pytest.mark.asyncio
async def test_create_lead_no_database_503(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings_leads_enabled(key="secret-leads-key")

    response = await client.post(
        "/v1/leads",
        json=LEAD_BODY,
        headers={"X-Leads-Key": "secret-leads-key"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_lead_invalid_email_422(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings_leads_enabled()

    response = await client.post(
        "/v1/leads",
        json={**LEAD_BODY, "email": "not-an-email"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_lead_honeypot_accepts_silently(app: FastAPI, client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: _settings_leads_enabled()

    response = await client.post(
        "/v1/leads",
        json={**LEAD_BODY, "website": "http://spam.example"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()["id"] == "discarded"


@pytest.mark.asyncio
async def test_create_lead_persists_and_dedupes_email() -> None:
    pytest.importorskip("asyncpg")
    database_url = Settings().database_url
    if not database_url:
        pytest.skip("DATABASE_URL not set")

    get_settings.cache_clear()
    app = create_app()

    def settings_with_leads() -> Settings:
        return Settings.model_construct(
            leads_enabled=True,
            leads_key="integration-leads-key",
            database_url=database_url,
        )

    app.dependency_overrides[get_settings] = settings_with_leads

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        headers = {"X-Leads-Key": "integration-leads-key"}
        body = {
            **LEAD_BODY,
            "email": "ops@harbour.example",
            "message": "Interested in charter dispute workflow.",
        }
        first = await client.post("/v1/leads", json=body, headers=headers)
        second = await client.post("/v1/leads", json=body, headers=headers)

    app.dependency_overrides.clear()
    get_settings.cache_clear()

    assert first.status_code == 201
    payload = first.json()
    assert payload["status"] == "received"
    assert payload["id"] != "discarded"
    assert second.status_code == 429

    import asyncpg

    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=1)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT email, organization FROM pilot_leads WHERE id = $1::uuid", payload["id"])
    await pool.close()
    assert row is not None
    assert row["email"] == "ops@harbour.example"
