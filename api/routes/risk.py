"""Risk endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from database.db import get_db
from database.repository import Repository
from detection.risk import score_all_assets, score_asset
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/top")
async def get_top(n: int = Query(10, ge=1, le=100), session: AsyncSession = Depends(get_db)):
    results = []
    for aid in twin_graph.graph.nodes:
        db_id = twin_graph.db_id_for(aid)
        latest = await Repository(session).risk_scores.latest_for_asset(db_id)
        if latest:
            results.append({
                "asset_id": aid,
                "asset_type": twin_graph.graph.nodes[aid].get("asset_type"),
                "score": latest.score, "factors": latest.factors or {},
                "scored_at": latest.scored_at.isoformat(),
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"ranked": results[:n], "total_assets": twin_graph.size,
            "computed_at": datetime.now(timezone.utc).isoformat()}


@router.get("/asset/{asset_id}")
async def get_asset_risk(asset_id: str, session: AsyncSession = Depends(get_db)):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset_id '{asset_id}'")
    db_id = twin_graph.db_id_for(asset_id)
    latest = await Repository(session).risk_scores.latest_for_asset(db_id)
    if latest is None:
        result = await score_asset(session, asset_id, persist=True)
        return result
    return {"asset_id": asset_id, "score": latest.score,
            "factors": latest.factors or {}, "scored_at": latest.scored_at.isoformat()}


@router.post("/recompute")
async def recompute_all(session: AsyncSession = Depends(get_db)):
    results = await score_all_assets(session, persist=True)
    return {"recomputed": len(results), "total_assets": twin_graph.size,
            "top_5": results[:5]}


@router.get("/weights")
async def get_weights():
    return {
        "detections": settings.risk_weight_detections,
        "transitions": settings.risk_weight_transitions,
        "incidents": settings.risk_weight_incidents,
        "threat_intel": settings.risk_weight_threat_intel,
        "centrality": settings.risk_weight_centrality,
        "health": settings.risk_weight_health,
    }
