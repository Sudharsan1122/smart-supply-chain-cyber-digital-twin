"""Triage endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
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


@router.get("/metrics/rules")
async def rule_metrics(session: AsyncSession = Depends(get_db)):
    """Return precision, recall, F1, and counts grouped by rule."""
    stmt = (select(m.Detection.rule_id, m.Detection.detection_type, m.Triage.verdict, func.count())
            .join(m.Triage, m.Triage.detection_id == m.Detection.id)
            .group_by(m.Detection.rule_id, m.Detection.detection_type, m.Triage.verdict))
    rows = (await session.execute(stmt)).all()

    rule_counts = {}
    for r_id, det_type, verdict, cnt in rows:
        rule_name = r_id or (f"ML-{det_type}" if det_type else "ML-ANOMALY")
        if rule_name not in rule_counts:
            rule_counts[rule_name] = {"TP": 0, "FP": 0, "FN": 0, "TN": 0}
        rule_counts[rule_name][verdict] = rule_counts[rule_name].get(verdict, 0) + cnt

    standard_rules = [f"RULE-00{i}" for i in range(1, 10)] + ["ML-ANOMALY"]
    rules_out = []
    for r in standard_rules:
        c = rule_counts.get(r, {"TP": 0, "FP": 0, "FN": 0, "TN": 0})
        tp = c.get("TP", 0)
        fp = c.get("FP", 0)
        fn = c.get("FN", 0)
        p = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if tp > 0 else 0.0)
        r_val = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if tp > 0 else 0.0)
        f1 = (2 * p * r_val / (p + r_val)) if (p + r_val) > 0 else 0.0
        rules_out.append({
            "rule_id": r,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(p, 3),
            "recall": round(r_val, 3),
            "f1": round(f1, 3),
            "total": tp + fp + fn,
        })
    return {"rules": rules_out}

