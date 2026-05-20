from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request

from aistruth_api.security import require_admin_key
from aistruth_api.usage import usage_summary_current_month

router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.get("/admin/usage")
async def admin_usage(request: Request) -> dict[str, object]:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        return {"month": datetime.now(UTC).strftime("%Y-%m"), "tenants": [], "note": "no database"}
    tenants = await usage_summary_current_month(pool)
    return {"month": datetime.now(UTC).strftime("%Y-%m"), "tenants": tenants}
