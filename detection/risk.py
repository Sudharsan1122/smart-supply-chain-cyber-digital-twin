"""Phase 12 - Risk scoring."""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from database import models as m
from database.repository import Repository
from digital_twin.graph import twin_graph
from digital_twin.metrics import betweenness_centrality
from digital_twin.state_manager import twin_state

logger = logging.getLogger(__name__)

SEVERITY_WEIGHT = {"info": 0.05, "low": 0.20, "medium": 0.45, "high": 0.75, "critical": 1.00}
HEALTH_WEIGHT = {"good": 0.0, "unknown": 0.3, "degraded": 0.6, "at_risk": 0.8, "critical": 1.0}


async def _detection_component(session, db_id, window):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window)
    stmt = (select(m.Detection).where(m.Detection.asset_id == db_id)
            .where(m.Detection.detected_at >= cutoff))
    rows = list((await session.execute(stmt)).scalars().all())
    import math
    score = sum(SEVERITY_WEIGHT.get(d.severity, 0.2) * (d.confidence or 0.5) for d in rows)
    return min(1.0, math.log1p(score) / 3.0)


async def _incident_component(session, db_id, window):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window)
    stmt = (select(m.Incident).where(m.Incident.root_asset_id == db_id)
            .where(m.Incident.status == "open")
            .where(m.Incident.window_start >= cutoff))
    rows = list((await session.execute(stmt)).scalars().all())
    import math
    score = sum(SEVERITY_WEIGHT.get(i.severity, 0.2) * (i.confidence or 0.5) for i in rows)
    return min(1.0, math.log1p(score) / 2.5)


def _centrality_component(asset_id):
    bc = betweenness_centrality()
    if not bc:
        return 0.0
    max_bc = max(bc.values()) or 1.0
    return round(min(1.0, bc.get(asset_id, 0.0) / max_bc), 4)


def _health_component(asset_id):
    s = twin_state.get(asset_id) or {}
    return HEALTH_WEIGHT.get(s.get("health", "unknown"), 0.3)


async def compute_components(session, asset_id):
    window = settings.risk_window_seconds
    db_id = twin_graph.db_id_for(asset_id)
    det = await _detection_component(session, db_id, window)
    inc = await _incident_component(session, db_id, window)
    return {
        "detections": det, "transitions": 0.0, "incidents": inc,
        "threat_intel": 0.0, "centrality": _centrality_component(asset_id),
        "health": _health_component(asset_id),
    }


async def score_asset(session, asset_id, persist=True, model_version="phase12-v1"):
    factors = await compute_components(session, asset_id)
    score = round(min(100.0, max(0.0,
        (settings.risk_weight_detections * factors["detections"]
         + settings.risk_weight_transitions * factors["transitions"]
         + settings.risk_weight_incidents * factors["incidents"]
         + settings.risk_weight_threat_intel * factors["threat_intel"]
         + settings.risk_weight_centrality * factors["centrality"]
         + settings.risk_weight_health * factors["health"]) * 100
    )), 2)

    if persist:
        db_id = twin_graph.db_id_for(asset_id)
        repo = Repository(session)
        await repo.risk_scores.insert(asset_db_id=db_id, score=score,
                                      factors=factors, model_version=model_version)
        await session.commit()

    return {"asset_id": asset_id, "score": score, "factors": factors,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "model_version": model_version}


async def score_all_assets(session, persist=True):
    results = []
    for asset_id in list(twin_graph.graph.nodes):
        try:
            results.append(await score_asset(session, asset_id, persist=persist))
        except Exception as e:
            logger.exception("Risk failed for %s: %s", asset_id, e)
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
