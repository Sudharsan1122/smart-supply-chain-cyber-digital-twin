"""Isolated subprocess execution engine for what-if supply chain disruption simulations."""
from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from sqlalchemy.orm import Session

from app.config import settings
from app.models import SimulationRun
from app.schemas import SimulationRequest, SimulationResponse
from app.services.audit_service import event_bus
from app.services.db_service import db_service

_ISOLATED_SIM_SCRIPT = """
import json, sys
data = json.loads(sys.stdin.read())
nodes = data["nodes"]
scenario = data["scenario_type"]
target = data["target_node_code"]
sev = float(data["severity_pct"]) / 100.0
days = int(data["duration_days"])

eff_cap = 0.0
tot_demand = 0.0
for n in nodes:
    cap = float(n["capacity"]) + float(n["inventory"])
    dem = float(n["demand"]) * (days / 7.0)
    if n["node_code"] == target:
        if scenario in ("SUPPLIER_FAILURE", "PORT_CLOSURE"):
            cap *= (1.0 - sev)
        elif scenario == "DEMAND_SPIKE":
            dem *= (1.0 + sev)
    eff_cap += cap
    tot_demand += dem

unmet = max(0.0, round(tot_demand - eff_cap, 2))
served_pct = round(100.0 if tot_demand <= 0 else min(100.0, max(0.0, (tot_demand - unmet) / tot_demand * 100.0)), 2)
base_cost = eff_cap * 3.5 + unmet * 45.0 + days * 420.0
recs = [
    f"Re-route lanes bypassing {target} for {days} days",
    f"Activate safety stock buffer at regional warehouses (severity={int(sev*100)}%)",
    "Trigger MILP flow re-allocation across backup suppliers",
]
print(json.dumps({"service_level_pct": served_pct, "total_cost": round(base_cost, 2), "unmet_demand": unmet, "recommendations": recs}))
"""


def _execute_isolated_worker(worker_input: dict[str, object]) -> dict[str, object]:
    """Run simulation mathematics in an isolated Python subprocess with timeout enforcement."""
    completed = subprocess.run(  # nosec B603
        [sys.executable, "-I", "-c", _ISOLATED_SIM_SCRIPT],
        input=json.dumps(worker_input),
        text=True,
        capture_output=True,
        timeout=settings.simulation_timeout_seconds,
        check=True,
    )
    result: dict[str, object] = json.loads(completed.stdout.strip())
    return result


def run_disruption_simulation(
    db: Session,
    payload: SimulationRequest,
    actor: str,
) -> SimulationResponse:
    """Execute a what-if disruption scenario in an isolated subprocess and record the outcome.

    Args:
        db: Active SQLAlchemy session.
        payload: Validated SimulationRequest parameters.
        actor: Authenticated username.

    Returns:
        SimulationResponse containing service level, cost, unmet demand, and recommendations.
    """
    db_service.seed_initial_data(db)
    nodes = [
        {"node_code": n.node_code, "capacity": n.capacity, "inventory": n.inventory, "demand": n.demand}
        for n in db_service.list_nodes(db)
    ]
    sim_out = _execute_isolated_worker(
        {
            "nodes": nodes,
            "scenario_type": payload.scenario_type.value,
            "target_node_code": payload.target_node_code,
            "severity_pct": payload.severity_pct,
            "duration_days": payload.duration_days,
        }
    )
    recs = [str(r) for r in sim_out.get("recommendations", [])]
    record = SimulationRun(
        scenario_type=payload.scenario_type.value,
        target_node_code=payload.target_node_code,
        severity_pct=payload.severity_pct,
        duration_days=payload.duration_days,
        status="COMPLETED",
        service_level_pct=float(sim_out["service_level_pct"]),
        total_cost=float(sim_out["total_cost"]),
        unmet_demand=float(sim_out["unmet_demand"]),
        summary_json=json.dumps({"recommendations": recs}),
        created_by=actor,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    event_bus.publish(
        db,
        {
            "actor": actor,
            "action": "SIMULATION_COMPLETED",
            "resource": payload.target_node_code,
            "details": {"scenario": payload.scenario_type.value, "service_level_pct": record.service_level_pct},
        },
    )
    return SimulationResponse(
        id=record.id,
        scenario_type=record.scenario_type,
        target_node_code=record.target_node_code,
        severity_pct=record.severity_pct,
        duration_days=record.duration_days,
        status=record.status,
        service_level_pct=record.service_level_pct,
        total_cost=record.total_cost,
        unmet_demand=record.unmet_demand,
        recommendations=recs,
    )
