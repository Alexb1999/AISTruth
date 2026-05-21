"""Public pilot lead capture from marketing site."""

from __future__ import annotations

import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from aistruth_api.config import Settings, get_settings
from aistruth_api.rate_limit import leads_rate_limit_key, limiter
from aistruth_api.schemas import PilotLeadCreate, PilotLeadResponse

router = APIRouter(tags=["leads"])
log = logging.getLogger(__name__)

LEADS_KEY_HEADER = "X-Leads-Key"


def _assert_leads_enabled(settings: Settings) -> None:
    if not settings.leads_enabled:
        raise HTTPException(status_code=404, detail="Not found")


def _require_leads_access(request: Request, settings: Settings) -> None:
    _assert_leads_enabled(settings)
    expected = settings.leads_key
    if not expected:
        return
    provided = request.headers.get(LEADS_KEY_HEADER)
    if provided is None or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid X-Leads-Key")


async def leads_access_guard(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    _require_leads_access(request, settings)


@router.post(
    "/leads",
    response_model=PilotLeadResponse,
    status_code=201,
    dependencies=[Depends(leads_access_guard)],
)
@limiter.limit("3/hour", key_func=leads_rate_limit_key)
async def create_pilot_lead(request: Request, body: PilotLeadCreate) -> PilotLeadResponse:
    """Store a pilot inquiry from the marketing contact form.

    Disabled unless ``AISTRUTH_LEADS_ENABLED=true``. When ``AISTRUTH_LEADS_KEY`` is set,
    callers must send a matching ``X-Leads-Key`` (typically via the Next.js ``/api/leads`` proxy).
    """
    if body.website:
        log.info("pilot_lead_honeypot_rejected email=%s", body.email)
        return PilotLeadResponse(id="discarded", status="received")

    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="Lead capture is unavailable — DATABASE_URL not configured on API.",
        )

    email = body.email.strip().lower()

    async with pool.acquire() as conn:
        recent = await conn.fetchval(
            """
            SELECT 1 FROM pilot_leads
            WHERE email = $1 AND created_at > now() - interval '1 hour'
            LIMIT 1
            """,
            email,
        )
        if recent is not None:
            raise HTTPException(
                status_code=429,
                detail="A submission for this email was received recently. Try again later.",
            )

        row = await conn.fetchrow(
            """
            INSERT INTO pilot_leads (
                name, organization, email, region, fleet_size, ais_feed, message
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            body.name.strip(),
            body.organization.strip(),
            email,
            body.region.strip(),
            body.fleet_size.strip() if body.fleet_size else None,
            body.ais_feed.strip() if body.ais_feed else None,
            body.message.strip() if body.message else None,
        )

    lead_id = str(row["id"])
    log.info(
        "pilot_lead_created id=%s org=%s region=%s ais_feed=%s",
        lead_id,
        body.organization,
        body.region,
        body.ais_feed,
    )
    return PilotLeadResponse(id=lead_id)
