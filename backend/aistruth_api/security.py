from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from aistruth_api.config import Settings, get_settings

API_KEY_HEADER = "X-AIS-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def _configured_api_keys(settings: Settings) -> list[str]:
    return [key.strip() for key in settings.api_keys.split(",") if key.strip()]


async def require_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require an API key on protected routes when AISTRUTH_API_KEYS is configured."""
    allowed = _configured_api_keys(settings)
    if not allowed:
        request.state.api_key_id = "auth-disabled"
        return
    if api_key is not None and any(hmac.compare_digest(api_key, key) for key in allowed):
        request.state.api_key_id = f"key:{allowed.index(api_key)}"
        return
    raise HTTPException(status_code=401, detail="Missing or invalid X-AIS-Key")
