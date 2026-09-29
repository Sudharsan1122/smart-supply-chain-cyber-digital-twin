"""
Background loop: pushes our twin state to Eclipse Ditto every 5 seconds.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from api_sources.ditto_adapter import ditto_adapter
from database.db import AsyncSessionLocal
from database.repository import Repository
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state

logger = logging.getLogger("uvicorn.error")

SYNC_INTERVAL = 5.0


async def sync_once() -> int:
    """Push all 32 assets to Ditto."""
    if not await ditto_adapter.health():
        logger.warning("Ditto not reachable — skipping sync")
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        assets = await repo.assets.list(limit=200)

        payloads = []
        for asset_row in assets:
            asset_id = asset_row.asset_id
            state = twin_state.get(asset_id) or {}
            risk_db = await repo.risk_scores.latest_for_asset(asset_row.id)
            parent_code = twin_graph.asset_id_for(asset_row.parent_id) if asset_row.parent_id else None
            meta_loc = (asset_row.metadata_ or {}).get("location") or {}
            pos = state.get("position") or meta_loc or {}

            payloads.append({
                "asset_id": asset_id,
                "asset_type": asset_row.asset_type,
                "name": asset_row.name,
                "parent": parent_code,
                "state": state.get("state") or asset_row.state or "unknown",
                "health": state.get("health") or asset_row.health or "unknown",
                "position": pos,
                "metrics": state.get("metrics") or {},
                "risk_score": float(risk_db.score) if risk_db else 0.0,
                "created_at": asset_row.created_at.isoformat() if asset_row.created_at else None,
            })

    async with httpx.AsyncClient(auth=ditto_adapter.auth, timeout=15.0) as client:
        for p in payloads:
            ok = await ditto_adapter.upsert_thing(p, client=client)
            if ok:
                count += 1

    logger.info("Ditto sync: pushed %d things", count)
    return count


async def ditto_sync_loop() -> None:
    """Runs forever, syncing every 5 seconds."""
    while True:
        try:
            await asyncio.sleep(SYNC_INTERVAL)
            await sync_once()
        except asyncio.CancelledError:
            logger.info("Ditto sync loop cancelled")
            break
        except Exception as e:
            logger.exception("Ditto sync error: %s", e)
