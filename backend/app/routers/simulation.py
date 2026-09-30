"""Simulation router with rate limiting and RBAC for what-if disruption scenarios."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import SimulationRequest, SimulationResponse
from app.security import RoleEnum, get_current_principal, require_role
from app.simulation.runner import run_disruption_simulation

router = APIRouter(tags=["simulation"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/simulate", response_model=SimulationResponse)
@limiter.limit("20/minute")
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def execute_simulation(
    request: Request,
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> SimulationResponse:
    """Execute an isolated what-if disruption simulation (rate-limited to prevent DoS)."""
    _ = request
    return run_disruption_simulation(db, payload, actor=str(principal["sub"]))
