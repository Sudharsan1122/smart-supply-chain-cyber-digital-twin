"""Bidirectional synchronization engine reconciling physical telemetry with Digital Twin state."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.digital_twin.event_trigger import evaluate_and_trigger_reoptimization
from app.schemas import SupplyNodeRead, TelemetrySyncPayload
from app.services.audit_service import event_bus
from app.services.db_service import db_service


class SyncEngine:
    """Synchronizes real-time physical sensor telemetry into the digital twin and emits feedback."""

    def synchronize_telemetry(
        self,
        db: Session,
        payload: TelemetrySyncPayload,
        actor: str,
    ) -> dict[str, object]:
        """Apply incoming node telemetry, audit the state transition, and evaluate >5% drift triggers.

        Args:
            db: Active SQLAlchemy session.
            payload: Validated TelemetrySyncPayload.
            actor: Authenticated principal or sensor ID.

        Returns:
            Dictionary with updated node state and auto-reoptimization trigger outcome.
        """
        node = db_service.get_node_by_code(db, payload.node_code)
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supply node {payload.node_code} not found",
            )
        prev_demand = float(node.demand)
        prev_capacity = float(node.capacity)
        if payload.inventory is not None:
            node.inventory = payload.inventory
        if payload.demand is not None:
            node.demand = payload.demand
        if payload.capacity is not None:
            node.capacity = payload.capacity
        db.commit()
        db.refresh(node)

        event_bus.publish(
            db,
            {
                "actor": actor,
                "action": "TWIN_TELEMETRY_SYNC",
                "resource": node.node_code,
                "details": {"inventory": node.inventory, "demand": node.demand, "capacity": node.capacity},
            },
        )
        trigger_info = evaluate_and_trigger_reoptimization(
            db=db,
            node_code=node.node_code,
            prev_demand=prev_demand,
            new_demand=float(node.demand),
            prev_capacity=prev_capacity,
            new_capacity=float(node.capacity),
            actor=actor,
        )
        return {
            "node": SupplyNodeRead.model_validate(node).model_dump(),
            "reoptimization": trigger_info,
        }


sync_engine = SyncEngine()
