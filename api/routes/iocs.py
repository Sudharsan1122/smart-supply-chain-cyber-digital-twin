"""IOC endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db
from database.repository import Repository
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/iocs", tags=["iocs"])


@router.get("")
async def list_iocs(ioc_type: str | None = Query(None), limit: int = Query(200, ge=1, le=1000),
                    session: AsyncSession = Depends(get_db)):
    stmt = select(m.IOC).order_by(m.IOC.last_seen.desc()).limit(limit)
    if ioc_type:
        stmt = stmt.where(m.IOC.ioc_type == ioc_type)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": r.id, "value": r.value, "ioc_type": r.ioc_type,
             "source": r.source, "confidence": r.confidence,
             "last_seen": r.last_seen.isoformat()} for r in rows]


@router.get("/summary")
async def summary(session: AsyncSession = Depends(get_db)):
    total = (await session.execute(select(func.count()).select_from(m.IOC))).scalar() or 0
    rows = (await session.execute(select(m.IOC.ioc_type, func.count()).group_by(m.IOC.ioc_type))).all()
    return {"total": total, "by_type": dict(rows)}


@router.get("/{ioc_id}")
async def get_ioc(ioc_id: int, session: AsyncSession = Depends(get_db)):
    row = await session.get(m.IOC, ioc_id)
    if row is None:
        raise HTTPException(404, "IOC not found")
    return {"id": row.id, "value": row.value, "ioc_type": row.ioc_type,
            "confidence": row.confidence, "source": row.source}
