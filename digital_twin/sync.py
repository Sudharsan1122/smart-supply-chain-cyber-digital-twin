"""Phase 8 - Sync + drift detection."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    computed_at: str
    db_asset_count: int
    twin_asset_count: int
    node_drifts: list[dict[str, Any]] = field(default_factory=list)
    state_drifts: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.node_drifts or self.state_drifts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "computed_at": self.computed_at,
            "has_drift": self.has_drift,
            "db_asset_count": self.db_asset_count,
            "twin_asset_count": self.twin_asset_count,
            "node_drifts": self.node_drifts,
            "state_drifts": self.state_drifts,
        }


async def compute_drift(session: AsyncSession) -> DriftReport:
    stmt = select(m.Asset).order_by(m.Asset.asset_id)
    db_assets = (await session.execute(stmt)).scalars().all()
    db_ids = {a.asset_id for a in db_assets}
    twin_ids = set(twin_graph.graph.nodes)

    node_drifts = []
    for aid in db_ids - twin_ids:
        node_drifts.append({"asset_id": aid, "reason": "added"})
    for aid in twin_ids - db_ids:
        node_drifts.append({"asset_id": aid, "reason": "removed"})

    return DriftReport(
        computed_at=datetime.now(timezone.utc).isoformat(),
        db_asset_count=len(db_assets),
        twin_asset_count=twin_graph.size,
        node_drifts=node_drifts,
    )


async def reconcile(session: AsyncSession) -> dict[str, Any]:
    before = twin_graph.size
    await twin_graph.reload_from_db(session)
    await twin_state.load_from_db(session)
    return {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "nodes_added": max(0, twin_graph.size - before),
        "nodes_removed": max(0, before - twin_graph.size),
        "states_refreshed": len(twin_state.all()),
        "errors": [],
    }


async def full_sync(session: AsyncSession) -> Any:
    class SyncResult:
        def __init__(self, d): self._d = d
        def to_dict(self): return self._d
        @property
        def errors(self): return self._d.get("errors", [])
    return SyncResult(await reconcile(session))
