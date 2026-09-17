"""Phase 10 - Detection engine."""
from __future__ import annotations
import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import Repository
from detection.context import build_context
from detection.rules import DetectionCandidate, all_rules

logger = logging.getLogger(__name__)


async def run_detection(session: AsyncSession, payload: Any,
                        validation_flags=None) -> list[dict[str, Any]]:
    ctx = await build_context(session, payload, validation_flags=validation_flags)
    candidates = []
    for rule_id, fn in all_rules().items():
        try:
            candidates.extend(fn(ctx) or [])
        except Exception as e:
            logger.exception("Rule %s failed: %s", rule_id, e)

    deduped = {}
    for c in candidates:
        deduped[(c.rule_id, c.title)] = c

    repo = Repository(session)
    results = []
    for c in deduped.values():
        det = await repo.detections.insert(
            asset_db_id=ctx.asset_db_id, detection_type="rule",
            rule_id=c.rule_id, severity=c.severity,
            confidence=c.confidence, description=c.description,
        )
        results.append({
            "detection_id": det.id, "rule_id": c.rule_id,
            "title": c.title, "severity": c.severity,
            "confidence": c.confidence, "evidence": c.evidence,
            "detection_type": "rule",
        })
    return results
