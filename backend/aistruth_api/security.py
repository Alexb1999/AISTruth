from __future__ import annotations

import hmac
from typing import TYPE_CHECKING
from uuid import UUID

import asyncpg
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from aistruth_api.config import Settings, get_settings
from aistruth_api.integrations.ais_resolver import effective_ais_source
from aistruth_api.tenants import ApiKeyAuth, TenantRecord, lookup_auth_by_raw_key

if TYPE_CHECKING:
    pass

API_KEY_HEADER = "X-AIS-Key"
ADMIN_KEY_HEADER = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
admin_key_header = APIKeyHeader(name=ADMIN_KEY_HEADER, auto_error=False)


def _configured_api_keys(settings: Settings) -> list[str]:
    return [key.strip() for key in settings.api_keys.split(",") if key.strip()]


def get_tenant(request: Request) -> TenantRecord | None:
    return getattr(request.state, "tenant", None)


def get_tenant_id(request: Request) -> UUID | None:
    return getattr(request.state, "tenant_id", None)


async def require_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Resolve tenant from DB key hash, then env allow-list; disable auth when both empty."""
    pool: asyncpg.Pool | None = getattr(request.app.state, "db_pool", None)
    request.state.tenant = None
    request.state.tenant_id = None
    request.state.api_key_id = None
    request.state.auth_mode = "anonymous"

    if api_key and pool is not None:
        async with pool.acquire() as conn:
            auth = await lookup_auth_by_raw_key(conn, api_key)
        if auth is not None:
            request.state.tenant = auth.tenant
            request.state.tenant_id = auth.tenant.id
            request.state.api_key_id = auth.api_key_id
            request.state.api_key_id_label = str(auth.api_key_id)
            request.state.auth_mode = "tenant_key"
            return

    allowed = _configured_api_keys(settings)
    if not allowed:
        request.state.api_key_id = "auth-disabled"
        request.state.auth_mode = "disabled"
        return

    if api_key is not None and any(hmac.compare_digest(api_key, key) for key in allowed):
        request.state.api_key_id = f"env:{allowed.index(api_key)}"
        request.state.auth_mode = "env_key"
        return

    raise HTTPException(status_code=401, detail="Missing or invalid X-AIS-Key")


async def require_admin_key(
    admin_key: str | None = Security(admin_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.admin_key
    if not expected:
        raise HTTPException(status_code=503, detail="AISTRUTH_ADMIN_KEY is not configured")
    if admin_key is None or not hmac.compare_digest(admin_key, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid X-Admin-Key")


def barentswatch_configured(settings: Settings) -> bool:
    return bool(settings.barentswatch_client_id and settings.barentswatch_client_secret)


def assert_barentswatch_access_allowed(
    request: Request,
    settings: Settings,
    tenant: TenantRecord | None,
) -> None:
    """Reject anonymous callers before any server-side BarentsWatch upstream call."""
    if effective_ais_source(settings, tenant) != "barentswatch":
        return
    if not barentswatch_configured(settings):
        return
    if settings.barentswatch_allow_anonymous:
        return
    auth_mode = getattr(request.state, "auth_mode", "anonymous")
    if auth_mode in ("tenant_key", "env_key"):
        return
    raise HTTPException(
        status_code=401,
        detail=(
            "Valid X-AIS-Key required to use BarentsWatch AIS on this deployment. "
            "Provision a tenant key or set AISTRUTH_API_KEYS for operator access."
        ),
    )


async def require_barentswatch_tenant(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Guard Norway proxy routes: authenticated callers with BarentsWatch AIS only."""
    assert_barentswatch_access_allowed(request, settings, get_tenant(request))
    tenant = get_tenant(request)
    if effective_ais_source(settings, tenant) != "barentswatch":
        raise HTTPException(
            status_code=403,
            detail=(
                "Norway BarentsWatch routes require ais_source=barentswatch for this tenant. "
                "File replay and Spire tenants should validate by MMSI directly."
            ),
        )
