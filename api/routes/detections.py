"""Detection queries."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("")
async def list_detections(severity: str | None = Query(None), rule_id: str | None = Query(None),
                          limit: int = Query(100, ge=1, le=1000),
                          session: AsyncSession = Depends(get_db)):
    stmt = select(m.Detection).order_by(m.Detection.detected_at.desc()).limit(limit)
    if severity:
        stmt = stmt.where(m.Detection.severity == severity)
    if rule_id:
        stmt = stmt.where(m.Detection.rule_id == rule_id)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": d.id, "asset_db_id": d.asset_id,
             "asset_code": twin_graph.asset_id_for(d.asset_id),
             "rule_id": d.rule_id, "severity": d.severity,
             "confidence": d.confidence, "description": d.description,
             "detection_type": d.detection_type,
             "detected_at": d.detected_at.isoformat()} for d in rows]


@router.get("/summary")
async def summary(session: AsyncSession = Depends(get_db)):
    total = (await session.execute(select(func.count()).select_from(m.Detection))).scalar() or 0
    sev_rows = (await session.execute(
        select(m.Detection.severity, func.count()).group_by(m.Detection.severity))).all()
    rule_rows = (await session.execute(
        select(m.Detection.rule_id, func.count()).where(m.Detection.rule_id.is_not(None))
        .group_by(m.Detection.rule_id))).all()
    return {"total": total, "by_severity": dict(sev_rows), "by_rule": dict(rule_rows)}


@router.get("/{asset_id}")
async def detections_for_asset(asset_id: str, limit: int = Query(100, ge=1, le=1000),
                                session: AsyncSession = Depends(get_db)):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset_id '{asset_id}'")
    db_id = twin_graph.db_id_for(asset_id)
    stmt = (select(m.Detection).where(m.Detection.asset_id == db_id)
            .order_by(m.Detection.detected_at.desc()).limit(limit))
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": d.id, "rule_id": d.rule_id, "severity": d.severity,
             "confidence": d.confidence, "description": d.description,
             "detected_at": d.detected_at.isoformat()} for d in rows]
