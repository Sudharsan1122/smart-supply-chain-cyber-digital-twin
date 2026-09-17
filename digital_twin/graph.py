"""Phase 3 - Digital Twin topology graph."""
from __future__ import annotations
import logging
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m

logger = logging.getLogger(__name__)


class DigitalTwinGraph:
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._asset_db_ids: dict[str, int] = {}
        self._loaded: bool = False

    async def reload_from_db(self, session: AsyncSession) -> None:
        self.graph.clear()
        self._asset_db_ids.clear()
        stmt = select(m.Asset).order_by(m.Asset.asset_id)
        rows = (await session.execute(stmt)).scalars().all()
        for a in rows:
            self.graph.add_node(
                a.asset_id,
                db_id=a.id, asset_type=a.asset_type,
                name=a.name, metadata=a.metadata_ or {},
            )
            self._asset_db_ids[a.asset_id] = a.id
        id_to_asset_id = {a.id: a.asset_id for a in rows}
        for a in rows:
            if a.parent_id is not None and a.parent_id in id_to_asset_id:
                self.graph.add_edge(id_to_asset_id[a.parent_id], a.asset_id, relation="contains")
        self._loaded = True
        logger.info("Twin graph: %d nodes, %d edges",
                    self.graph.number_of_nodes(), self.graph.number_of_edges())

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def size(self) -> int:
        return self.graph.number_of_nodes()

    def has_node(self, asset_id: str) -> bool:
        return self.graph.has_node(asset_id)

    def get_node(self, asset_id: str) -> dict[str, Any] | None:
        if not self.graph.has_node(asset_id):
            return None
        return {"asset_id": asset_id, **self.graph.nodes[asset_id]}

    def all_nodes(self) -> list[dict[str, Any]]:
        return [{"asset_id": n, **self.graph.nodes[n]} for n in self.graph.nodes]

    def db_id_for(self, asset_id: str) -> int | None:
        return self._asset_db_ids.get(asset_id)

    def asset_id_for(self, db_id: int) -> str | None:
        for aid, did in self._asset_db_ids.items():
            if did == db_id:
                return aid
        return None

    def direct_children(self, asset_id: str) -> list[str]:
        if not self.graph.has_node(asset_id):
            return []
        return list(self.graph.successors(asset_id))

    def direct_parents(self, asset_id: str) -> list[str]:
        if not self.graph.has_node(asset_id):
            return []
        return list(self.graph.predecessors(asset_id))

    def descendants(self, asset_id: str) -> list[str]:
        if not self.graph.has_node(asset_id):
            return []
        return list(nx.descendants(self.graph, asset_id))

    def ancestors(self, asset_id: str) -> list[str]:
        if not self.graph.has_node(asset_id):
            return []
        return list(nx.ancestors(self.graph, asset_id))

    def edges(self) -> list[dict[str, str]]:
        return [{"source": u, "target": v, **d}
                for u, v, d in self.graph.edges(data=True)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "nodes": self.all_nodes(),
            "edges": self.edges(),
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
        }


twin_graph = DigitalTwinGraph()
