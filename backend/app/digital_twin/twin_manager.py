"""Digital Twin manager providing holistic network topology and KPI state snapshots."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas import SupplyEdgeCreate, SupplyEdgeRead, SupplyNodeCreate, SupplyNodeRead
from app.services.audit_service import event_bus
from app.services.db_service import db_service


class TwinManager:
    """Coordinates read/write operations on the Supply Chain Digital Twin topology."""

    def get_network_snapshot(self, db: Session) -> dict[str, object]:
        """Return complete digital twin state including nodes, edges, and aggregate KPIs.

        Args:
            db: Active SQLAlchemy session.

        Returns:
            Dictionary containing nodes, edges, and summary metrics.
        """
        db_service.seed_initial_data(db)
        nodes = db_service.list_nodes(db)
        edges = db_service.list_edges(db)
        total_capacity = round(sum(n.capacity for n in nodes if n.is_open), 2)
        total_inventory = round(sum(n.inventory for n in nodes), 2)
        total_demand = round(sum(n.demand for n in nodes), 2)
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_capacity": total_capacity,
            "total_inventory": total_inventory,
            "total_demand": total_demand,
            "nodes": [SupplyNodeRead.model_validate(n).model_dump() for n in nodes],
            "edges": [SupplyEdgeRead.model_validate(e).model_dump() for e in edges],
        }

    def ingest_node(self, db: Session, payload: SupplyNodeCreate, actor: str) -> SupplyNodeRead:
        """Ingest or update a supply chain node and emit an audit event."""
        node = db_service.upsert_node(db, payload)
        event_bus.publish(
            db,
            {
                "actor": actor,
                "action": "NODE_INGESTED",
                "resource": node.node_code,
                "details": {"node_type": node.node_type, "capacity": node.capacity},
            },
        )
        return SupplyNodeRead.model_validate(node)

    def ingest_edge(self, db: Session, payload: SupplyEdgeCreate, actor: str) -> SupplyEdgeRead:
        """Ingest or update a transportation lane and emit an audit event."""
        edge = db_service.upsert_edge(db, payload)
        event_bus.publish(
            db,
            {
                "actor": actor,
                "action": "EDGE_INGESTED",
                "resource": edge.edge_code,
                "details": {"source": edge.source_node_code, "target": edge.target_node_code},
            },
        )
        return SupplyEdgeRead.model_validate(edge)


twin_manager = TwinManager()
