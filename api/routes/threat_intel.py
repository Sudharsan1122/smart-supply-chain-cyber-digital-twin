"""Threat intel endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from attack_story.enrichment import enrich_ioc, enrich_pending, verdict_weight
from database import models as m
from database.db import get_db

router = APIRouter(prefix="/threat-intel", tags=["threat-intel"])


@router.post("/enrich/{ioc_id}")
async def enrich_one(ioc_id: int, force: bool = Query(False),
                     session: AsyncSession = Depends(get_db)):
    row = await session.get(m.IOC, ioc_id)
    if row is None:
        raise HTTPException(404, "IOC not found")
    result = await enrich_ioc(session, row, force=force)
    await session.commit()
    return result


@router.post("/sweep")
async def sweep(limit: int = Query(20, ge=1, le=200), session: AsyncSession = Depends(get_db)):
    results = await enrich_pending(session, limit=limit)
    return {"processed": len(results), "results": results}


@router.get("/cache-stats")
async def cache_stats(session: AsyncSession = Depends(get_db)):
    total = (await session.execute(select(func.count()).select_from(m.IOC))).scalar() or 0
    enriched = (await session.execute(
        select(func.count(func.distinct(m.IOCEnrichment.ioc_id))))).scalar() or 0
    types = (await session.execute(select(m.IOC.ioc_type, func.count()).group_by(m.IOC.ioc_type))).all()
    return {"ttl_seconds": 86400, "total_iocs": total, "enriched_iocs": enriched,
            "unenriched_iocs": max(0, total - enriched), "by_type": dict(types)}
