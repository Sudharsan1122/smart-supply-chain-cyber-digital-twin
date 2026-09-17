"""Blast radius endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db
from digital_twin.blast_radius import compute_blast_radius, persist_blast_radius
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/blast-radius", tags=["blast-radius"])


@router.post("/compute")
async def compute(payload: dict, session: AsyncSession = Depends(get_db)):
    asset_id = payload.get("asset_id")
    if not asset_id or not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset '{asset_id}'")
    result = compute_blast_radius(asset_id, severity=payload.get("severity", "high"),
                                   max_depth=payload.get("max_depth", 5))
    if payload.get("persist", True):
        await persist_blast_radius(session, result)
        await session.commit()
    return {
        "source_asset_id": result.source_asset_id, "severity": result.source_severity,
        "max_depth": result.max_depth, "impacted_count": len(result.impacted),
        "total_impact": result.total_impact, "by_depth": result.by_depth,
        "critical_assets": result.critical_assets,
        "impacted": result.impacted[:200],
    }


@router.get("/source/{asset_id}")
async def get_for_source(asset_id: str, limit: int = Query(200),
                        session: AsyncSession = Depends(get_db)):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset")
    db_id = twin_graph.db_id_for(asset_id)
    stmt = (select(m.BlastRadius).where(m.BlastRadius.source_asset_id == db_id)
            .order_by(m.BlastRadius.computed_at.desc()).limit(limit))
    rows = (await session.execute(stmt)).scalars().all()
    return [{"impacted_asset": twin_graph.asset_id_for(r.impacted_asset_id),
             "depth": r.depth, "impact_score": r.impact_score} for r in rows]
