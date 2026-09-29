"""Eclipse Ditto integration endpoints."""
from fastapi import APIRouter, HTTPException

from api_sources.ditto_adapter import ditto_adapter

router = APIRouter(prefix="/ditto", tags=["ditto"])


@router.get("/status")
async def ditto_status():
    reachable = await ditto_adapter.health()
    items = await ditto_adapter.list_things(limit=200) if reachable else []
    return {
        "ditto_reachable": reachable,
        "base_url": ditto_adapter.base_url,
        "public_url": "http://localhost:8080",
        "namespace": ditto_adapter.namespace,
        "things_count": len(items),
    }


@router.get("/things")
async def list_ditto_things():
    return await ditto_adapter.list_things(limit=200)


@router.get("/things/{asset_id}")
async def get_thing(asset_id: str):
    thing = await ditto_adapter.get_thing(asset_id)
    if thing is None:
        raise HTTPException(404, f"Thing {asset_id} not found in Ditto")
    return thing


@router.post("/sync")
async def force_sync():
    from ingestion.ditto_sync import sync_once
    pushed = await sync_once()
    return {"status": "synced", "pushed": pushed}
