"""Phase 3+9 - Twin state manager."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import Repository
from digital_twin.graph import twin_graph

logger = logging.getLogger(__name__)


class TwinStateManager:
    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}

    async def load_from_db(self, session: AsyncSession) -> None:
        repo = Repository(session)
        rows = await repo.twin_states.list(limit=10_000)
        self._states.clear()
        for row in rows:
            asset_id = twin_graph.asset_id_for(row.asset_id)
            if asset_id is None:
                continue
            self._states[asset_id] = {
                "state": row.state, "health": row.health,
                "position": row.position or {}, "metrics": row.metrics or {},
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
            }
        logger.info("Loaded twin state for %d assets", len(self._states))

    def get(self, asset_id: str) -> dict[str, Any] | None:
        return self._states.get(asset_id)

    def all(self) -> dict[str, dict[str, Any]]:
        return dict(self._states)

    def summary(self) -> dict[str, Any]:
        by_state: dict[str, int] = {}
        by_health: dict[str, int] = {}
        for s in self._states.values():
            by_state[s["state"]] = by_state.get(s["state"], 0) + 1
            by_health[s["health"]] = by_health.get(s["health"], 0) + 1
        return {"total_assets": len(self._states),
                "by_state": by_state, "by_health": by_health}

    async def update_state(self, session: AsyncSession, asset_id: str, *,
                           state: str | None = None, health: str | None = None,
                           position: dict | None = None, metrics: dict | None = None,
                           transition_reason: str | None = None) -> dict[str, Any]:
        if not twin_graph.has_node(asset_id):
            raise ValueError(f"Unknown asset: {asset_id}")

        prev = self._states.get(asset_id) or {
            "state": "unknown", "health": "unknown",
            "position": {}, "metrics": {}, "last_seen": None,
        }
        prev_state = prev.get("state")

        new_state = state if state is not None else prev["state"]
        new_health = health if health is not None else prev["health"]
        new_position = position if position is not None else prev.get("position", {})
        new_metrics = {**prev.get("metrics", {}), **(metrics or {})}

        current = {
            "state": new_state, "health": new_health,
            "position": new_position, "metrics": new_metrics,
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        self._states[asset_id] = current

        db_id = twin_graph.db_id_for(asset_id)
        if db_id is not None:
            repo = Repository(session)
            await repo.twin_states.upsert(
                asset_db_id=db_id, state=new_state, health=new_health,
                position=new_position, metrics=new_metrics,
                last_seen=datetime.now(timezone.utc),
            )
            if prev_state != new_state and prev_state is not None:
                await repo.state_transitions.record(
                    asset_db_id=db_id, to_state=new_state,
                    from_state=prev_state, reason=transition_reason,
                )
            await session.commit()

        return current


twin_state = TwinStateManager()
