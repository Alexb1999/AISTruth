from __future__ import annotations

from slowapi import Limiter
from starlette.requests import Request


def client_ip(request: Request) -> str:
    """Best-effort client IP; honours first X-Forwarded-For hop when behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit_key(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is not None:
        return f"tenant:{tenant_id}"
    api_key = request.headers.get("X-AIS-Key")
    if api_key:
        return f"api-key:{api_key}"
    return f"ip:{client_ip(request)}"


def leads_rate_limit_key(request: Request) -> str:
    return f"leads:{client_ip(request)}"


limiter = Limiter(key_func=rate_limit_key)
