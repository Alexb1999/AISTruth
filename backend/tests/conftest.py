from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aistruth_api.config import get_settings
from aistruth_api.main import create_app


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    monkeypatch.setenv("AISTRUTH_ENABLE_GEODNET_DEBUG", "false")
    monkeypatch.setenv("AISTRUTH_API_KEYS", "")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_ID", "")
    monkeypatch.setenv("BARENTSWATCH_CLIENT_SECRET", "")
    for name in ("DATABASE_URL", "AISTRUTH_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    return create_app()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
