"""Asset query endpoints."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.repository import Repository
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("")
async def list_assets(
    asset_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_db),
):
    repo = Repository(session)
    if asset_type:
        rows = await repo.assets.list_by_type(asset_type, limit=limit)
    else:
        rows = await repo.assets.list(limit=limit)
    out: list[dict[str, Any]] = []
    for a in rows:
        st = twin_state.get(a.asset_id) or {}
        out.append({
            "asset_id": a.asset_id,
            "asset_type": a.asset_type,
            "name": a.name,
            "state": st.get("state"),
            "health": st.get("health"),
        })
    return out


@router.get("/{asset_id}")
async def get_asset(asset_id: str, session: AsyncSession = Depends(get_db)):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset_id '{asset_id}'")
    repo = Repository(session)
    a = await repo.assets.get_by_asset_id(asset_id)
    if a is None:
        raise HTTPException(404, f"Asset not in DB")
    return {
        "asset_id": a.asset_id,
        "asset_type": a.asset_type,
        "name": a.name,
        "state": twin_state.get(asset_id) or {},
        "graph": {
            "children": twin_graph.direct_children(asset_id),
            "parents": twin_graph.direct_parents(asset_id),
        },
    }
