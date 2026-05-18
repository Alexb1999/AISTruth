from __future__ import annotations

from slowapi import Limiter
from starlette.requests import Request


def rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("X-AIS-Key")
    if api_key:
        return f"api-key:{api_key}"
    client = request.client.host if request.client else "unknown"
    return f"ip:{client}"


limiter = Limiter(key_func=rate_limit_key)
