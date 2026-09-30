"""Optimization router with rate limiting and RBAC for MILP network optimization."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.optimization.solver import run_network_optimization
from app.optimization.storage_interface import SqlAlchemyOptimizationStorage
from app.schemas import OptimizationRequest, OptimizationResponse
from app.security import RoleEnum, get_current_principal, require_role

router = APIRouter(tags=["optimization"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/optimize", response_model=OptimizationResponse)
@limiter.limit("15/minute")
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def execute_optimization(
    request: Request,
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> OptimizationResponse:
    """Run PuLP MILP facility opening and flow allocation optimization."""
    _ = request
    storage = SqlAlchemyOptimizationStorage(db)
    res = run_network_optimization(
        storage=storage,
        trigger_reason=payload.trigger_reason,
        actor=str(principal["sub"]),
        demand_multiplier=payload.demand_multiplier,
    )
    return OptimizationResponse(
        id=res.id,
        trigger_reason=res.trigger_reason,
        status=res.status,
        objective_cost=res.objective_cost,
        open_facilities=res.open_facilities,
        flow_allocations=res.flow_allocations,
    )
