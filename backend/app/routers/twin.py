"""Digital Twin state router for topology queries, node/edge ingestion, and telemetry sync."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.digital_twin.sync_engine import sync_engine
from app.digital_twin.twin_manager import twin_manager
from app.schemas import (
    SupplyEdgeCreate,
    SupplyEdgeRead,
    SupplyNodeCreate,
    SupplyNodeRead,
    TelemetrySyncPayload,
)
from app.security import RoleEnum, get_current_principal, require_role

router = APIRouter(prefix="/twin", tags=["twin"])


@router.get("/state")
def get_twin_state(
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> dict[str, object]:
    """Return real-time digital twin network topology and KPI state."""
    _ = principal
    return twin_manager.get_network_snapshot(db)


@router.post("/nodes", response_model=SupplyNodeRead)
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def upsert_supply_node(
    payload: SupplyNodeCreate,
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> SupplyNodeRead:
    """Ingest or update a supply chain node (requires ADMIN or PLANNER role)."""
    return twin_manager.ingest_node(db, payload, actor=str(principal["sub"]))


@router.post("/edges", response_model=SupplyEdgeRead)
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def upsert_supply_edge(
    payload: SupplyEdgeCreate,
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> SupplyEdgeRead:
    """Ingest or update a supply chain transportation lane (requires ADMIN or PLANNER role)."""
    return twin_manager.ingest_edge(db, payload, actor=str(principal["sub"]))


@router.post("/sync")
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def synchronize_node_telemetry(
    payload: TelemetrySyncPayload,
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> dict[str, object]:
    """Synchronize live telemetry into the digital twin and auto-trigger MILP if drift > 5%."""
    return sync_engine.synchronize_telemetry(db, payload, actor=str(principal["sub"]))
