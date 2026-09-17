"""Digital twin endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.repository import Repository
from digital_twin import metrics as topo
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state
from digital_twin.sync import compute_drift, full_sync

router = APIRouter(prefix="/twin", tags=["twin"])


@router.get("/graph")
async def get_graph():
    return twin_graph.to_dict()


@router.get("/summary")
async def get_summary():
    return topo.graph_summary()


@router.get("/nodes")
async def list_nodes():
    return twin_graph.all_nodes()


@router.get("/neighbors/{asset_id}")
async def get_neighbors(asset_id: str):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset_id '{asset_id}'")
    return {
        "asset_id": asset_id,
        "children": twin_graph.direct_children(asset_id),
        "parents": twin_graph.direct_parents(asset_id),
        "descendants": twin_graph.descendants(asset_id),
        "ancestors": twin_graph.ancestors(asset_id),
    }


@router.get("/state")
async def get_all_states():
    return {"summary": twin_state.summary(), "states": twin_state.all()}


@router.get("/state/{asset_id}")
async def get_state(asset_id: str):
    s = twin_state.get(asset_id)
    if s is None:
        raise HTTPException(404, f"No state for {asset_id}")
    return {"asset_id": asset_id, **s}


@router.get("/metrics/critical")
async def get_critical(top_n: int = 5):
    return {"top": topo.critical_nodes(top_n=top_n)}


@router.get("/drift")
async def drift(session: AsyncSession = Depends(get_db)):
    report = await compute_drift(session)
    return report.to_dict()


@router.post("/sync")
async def sync(session: AsyncSession = Depends(get_db)):
    result = await full_sync(session)
    return result.to_dict()
