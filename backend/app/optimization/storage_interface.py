"""StorageInterface abstraction decoupling the MILP Optimizer from SQLAlchemy persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OptimizationRun, SupplyEdge, SupplyNode
from app.services.audit_service import event_bus
from app.services.db_service import db_service


@dataclass
class NodeData:
    """Pure domain value object for a supply chain node."""

    node_code: str
    node_type: str
    capacity: float
    fixed_cost: float
    inventory: float
    demand: float


@dataclass
class EdgeData:
    """Pure domain value object for a transportation lane."""

    edge_code: str
    source_node_code: str
    target_node_code: str
    lead_time_days: float
    unit_cost: float
    max_flow: float


@dataclass
class OptimizationResultData:
    """Pure domain value object representing a completed MILP optimization run."""

    id: int
    trigger_reason: str
    status: str
    objective_cost: float
    open_facilities: list[str]
    flow_allocations: dict[str, float]


class OptimizationStorageInterface(ABC):
    """Abstract storage contract injected into the MILP solver (Dependency Inversion Principle)."""

    @abstractmethod
    def load_network(self) -> tuple[list[NodeData], list[EdgeData]]:
        """Load current nodes and edges for MILP formulation."""

    @abstractmethod
    def save_result(
        self,
        trigger_reason: str,
        status: str,
        objective_cost: float,
        open_facilities: list[str],
        flow_allocations: dict[str, float],
        actor: str,
    ) -> OptimizationResultData:
        """Persist optimization outcome and emit domain event."""


class SqlAlchemyOptimizationStorage(OptimizationStorageInterface):
    """Concrete SQLAlchemy implementation of OptimizationStorageInterface."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def load_network(self) -> tuple[list[NodeData], list[EdgeData]]:
        """Fetch nodes and active edges via the DB facade."""
        db_service.seed_initial_data(self._db)
        nodes = [
            NodeData(
                node_code=n.node_code,
                node_type=n.node_type,
                capacity=float(n.capacity),
                fixed_cost=float(n.fixed_cost),
                inventory=float(n.inventory),
                demand=float(n.demand),
            )
            for n in self._db.execute(select(SupplyNode)).scalars().all()
        ]
        edges = [
            EdgeData(
                edge_code=e.edge_code,
                source_node_code=e.source_node_code,
                target_node_code=e.target_node_code,
                lead_time_days=float(e.lead_time_days),
                unit_cost=float(e.unit_cost),
                max_flow=float(e.max_flow),
            )
            for e in self._db.execute(select(SupplyEdge).where(SupplyEdge.is_active.is_(True))).scalars().all()
        ]
        return nodes, edges

    def save_result(
        self,
        trigger_reason: str,
        status: str,
        objective_cost: float,
        open_facilities: list[str],
        flow_allocations: dict[str, float],
        actor: str,
    ) -> OptimizationResultData:
        """Store OptimizationRun row and publish an audit event on the EventBus."""
        run = OptimizationRun(
            trigger_reason=trigger_reason,
            status=status,
            objective_cost=objective_cost,
            open_facilities_json=json.dumps(open_facilities),
            flow_allocations_json=json.dumps(flow_allocations),
            created_by=actor,
        )
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)
        event_bus.publish(
            self._db,
            {
                "actor": actor,
                "action": "MILP_OPTIMIZATION_EXECUTED",
                "resource": f"OPT-{run.id}",
                "details": {"trigger": trigger_reason, "status": status, "objective_cost": objective_cost},
            },
        )
        return OptimizationResultData(
            id=run.id,
            trigger_reason=trigger_reason,
            status=status,
            objective_cost=objective_cost,
            open_facilities=open_facilities,
            flow_allocations=flow_allocations,
        )
