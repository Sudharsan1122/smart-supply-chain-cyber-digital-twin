"""Phase 18 - Triage engine."""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database import models as m
from database.repository import Repository

logger = logging.getLogger(__name__)

SEVERITY_SCORE = {"info": 0.05, "low": 0.20, "medium": 0.50, "high": 0.80, "critical": 1.00}
VERDICT_SCORE = {"malicious": 1.0, "suspicious": 0.6, "clean": 0.0, "unknown": 0.2}


@dataclass
class TriageDecision:
    detection_id: int
    verdict: str
    confidence: float
    score: float
    reasons: list[str]


async def _sig_severity(session, det):
    s = SEVERITY_SCORE.get(det.severity, 0.3)
    return (s, f"sev={det.severity}") if det.severity in ("high", "critical") else (s, None)


async def _sig_confidence(session, det):
    c = det.confidence if det.confidence is not None else 0.5
    return c, (f"conf={c:.2f}" if c >= 0.75 else None)


async def _sig_story_bonus(session, det):
    stmt = (select(m.AttackStory)
            .where(m.AttackStory.started_at <= det.detected_at)
            .where(m.AttackStory.ended_at >= det.detected_at)
            .where(m.AttackStory.status.in_(["analyzed", "completed", "running"]))
            .limit(1))
    story = (await session.execute(stmt)).scalars().first()
    return (1.0, f"story={story.attack_id[:8]}") if story else (0.0, None)


async def score_detection(session, det):
    sev, r1 = await _sig_severity(session, det)
    conf, r2 = await _sig_confidence(session, det)
    story, r3 = await _sig_story_bonus(session, det)

    weighted = (settings.triage_weight_severity * sev
                + settings.triage_weight_confidence * conf)
    if story > 0:
        weighted += settings.triage_story_bonus

    score = round(min(1.0, weighted), 4)
    verdict = "TP" if score >= settings.triage_tp_threshold else "FP"
    reasons = [r for r in (r1, r2, r3) if r]
    dist = abs(score - settings.triage_tp_threshold)
    conf_label = round(min(0.99, 0.5 + dist * 1.5), 3)

    return TriageDecision(det.id, verdict, conf_label, score, reasons)


async def triage_detection(session, detection_db_id, analyst=None, override_verdict=None, notes=None):
    det = await session.get(m.Detection, detection_db_id)
    if det is None:
        raise ValueError(f"Detection {detection_db_id} not found")

    if override_verdict:
        decision = TriageDecision(detection_db_id, override_verdict, 1.0,
                                   1.0 if override_verdict == "TP" else 0.0,
                                   ["analyst_override"])
    else:
        decision = await score_detection(session, det)

    repo = Repository(session)
    row = await repo.triage.classify(
        detection_db_id=detection_db_id, verdict=decision.verdict,
        confidence=decision.confidence, analyst=analyst,
        notes=notes or " | ".join(decision.reasons),
    )
    await session.flush()
    return {"triage_id": row.id, "detection_id": detection_db_id,
            "verdict": decision.verdict, "confidence": decision.confidence,
            "score": decision.score, "reasons": decision.reasons}


async def triage_pending(session, limit=50):
    triaged = select(m.Triage.detection_id)
    stmt = (select(m.Detection).where(m.Detection.id.not_in(triaged))
            .order_by(m.Detection.detected_at.desc()).limit(limit))
    candidates = list((await session.execute(stmt)).scalars().all())
    results = []
    for det in candidates:
        try:
            results.append(await triage_detection(session, det.id))
        except Exception as e:
            logger.exception("Triage failed: %s", e)
    if candidates:
        await session.commit()
    return results


async def global_metrics(session):
    stmt = select(m.Triage.verdict, func.count()).group_by(m.Triage.verdict)
    counts = {v: n for v, n in (await session.execute(stmt)).all()}
    tp = counts.get("TP", 0)
    fp = counts.get("FP", 0)
    fn = counts.get("FN", 0)
    tn = counts.get("TN", 0)
    total = tp + fp + fn + tn
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    acc = (tp + tn) / total if total > 0 else 0.0
    return {"total": total, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(p, 3), "recall": round(r, 3),
            "f1": round(f1, 3), "accuracy": round(acc, 3)}
