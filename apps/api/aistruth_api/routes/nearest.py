from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["spatial"])


@router.get("/nearest-node")
async def nearest_node(request: Request, lat: float, lon: float) -> dict[str, object]:
    """Return nearest fixture `geodnet_nodes` row using PostGIS geography ordering."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL not set or pool unavailable. Start docker compose and export DATABASE_URL.",
        )
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="lat/lon out of range")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id,
                   name,
                   ST_Distance(
                       geom,
                       ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
                   ) AS dist_m
            FROM geodnet_nodes
            WHERE active
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
            LIMIT 1
            """,
            lon,
            lat,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="No active nodes in database")
    return {
        "id": row["id"],
        "name": row["name"],
        "distance_m": float(row["dist_m"]),
        "query": {"lat": lat, "lon": lon},
    }
