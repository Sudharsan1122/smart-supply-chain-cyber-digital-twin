"""Triage endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db
from detection.triage import global_metrics, triage_detection, triage_pending

router = APIRouter(prefix="/triage", tags=["triage"])


@router.get("")
async def list_triage(verdict: str | None = Query(None), limit: int = Query(100, ge=1, le=1000),
                     session: AsyncSession = Depends(get_db)):
    stmt = (select(m.Triage, m.Detection).join(m.Detection, m.Detection.id == m.Triage.detection_id)
            .order_by(m.Triage.created_at.desc()).limit(limit))
    if verdict:
        stmt = stmt.where(m.Triage.verdict == verdict)
    rows = (await session.execute(stmt)).all()
    return [{"id": t.id, "detection_id": t.detection_id, "verdict": t.verdict,
             "confidence": t.confidence, "analyst": t.analyst, "notes": t.notes,
             "rule_id": d.rule_id, "severity": d.severity,
             "created_at": t.created_at.isoformat()} for t, d in rows]


@router.post("/run")
async def run(payload: dict, session: AsyncSession = Depends(get_db)):
    det_id = payload.get("detection_id")
    if not det_id:
        raise HTTPException(400, "detection_id required")
    try:
        result = await triage_detection(session, det_id,
                                        analyst=payload.get("analyst"),
                                        override_verdict=payload.get("verdict"),
                                        notes=payload.get("notes"))
        await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/sweep")
async def sweep(limit: int = Query(50, ge=1, le=500), session: AsyncSession = Depends(get_db)):
    results = await triage_pending(session, limit=limit)
    return {"processed": len(results), "results": results}


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_db)):
    return await global_metrics(session)
