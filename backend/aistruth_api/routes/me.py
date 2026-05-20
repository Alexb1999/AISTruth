from __future__ import annotations

from fastapi import APIRouter, Request

from aistruth_api.security import get_tenant
from aistruth_api.tenants import tenant_public_dict

router = APIRouter(tags=["identity"])


@router.get("/me")
async def whoami(request: Request) -> dict[str, object]:
    tenant = get_tenant(request)
    if tenant is None:
        return {
            "authenticated": request.state.auth_mode != "anonymous",
            "auth_mode": getattr(request.state, "auth_mode", "anonymous"),
            "tenant": None,
        }
    return {
        "authenticated": True,
        "auth_mode": getattr(request.state, "auth_mode", "tenant_key"),
        "tenant": tenant_public_dict(tenant),
    }
