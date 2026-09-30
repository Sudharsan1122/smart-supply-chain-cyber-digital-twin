"""Drift detection trigger that initiates automatic MILP re-optimization when delta > 5%."""
from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.config import settings
from app.optimization.solver import run_network_optimization
from app.optimization.storage_interface import SqlAlchemyOptimizationStorage
from app.services.audit_service import event_bus

logger = logging.getLogger(__name__)


def compute_relative_delta_pct(previous_value: float, new_value: float) -> float:
    """Compute percentage change between previous and new telemetry values.

    Args:
        previous_value: Baseline metric value.
        new_value: Updated metric value.

    Returns:
        Absolute relative delta percentage.
    """
    if previous_value <= 0.0:
        return 100.0 if new_value > 0.0 else 0.0
    return round(abs(new_value - previous_value) / previous_value * 100.0, 2)


def evaluate_and_trigger_reoptimization(
    db: Session,
    node_code: str,
    prev_demand: float,
    new_demand: float,
    prev_capacity: float,
    new_capacity: float,
    actor: str,
) -> dict[str, object]:
    """Check if demand or capacity drifted >5% and automatically run MILP re-optimization.

    Args:
        db: Active SQLAlchemy session.
        node_code: Updated supply node code.
        prev_demand: Previous demand level.
        new_demand: Updated demand level.
        prev_capacity: Previous capacity level.
        new_capacity: Updated capacity level.
        actor: Principal or sensor identifier.

    Returns:
        Dictionary describing drift percentages and whether re-optimization was triggered.
    """
    demand_delta = compute_relative_delta_pct(prev_demand, new_demand)
    capacity_delta = compute_relative_delta_pct(prev_capacity, new_capacity)
    max_delta = max(demand_delta, capacity_delta)
    threshold = settings.reoptimize_threshold_pct
    if max_delta <= threshold:
        return {"triggered": False, "max_delta_pct": max_delta, "optimization_id": None}

    reason = f"AUTO_DRIFT_{node_code}_{max_delta:.1f}PCT"
    event_bus.publish(
        db,
        {
            "actor": actor,
            "action": "AUTO_REOPTIMIZE_TRIGGERED",
            "resource": node_code,
            "details": {"demand_delta_pct": demand_delta, "capacity_delta_pct": capacity_delta},
        },
    )
    storage = SqlAlchemyOptimizationStorage(db)
    opt_run = run_network_optimization(storage, trigger_reason=reason, actor=actor)
    logger.info("Auto re-optimization completed for %s (delta=%.2f%%)", node_code, max_delta)
    return {"triggered": True, "max_delta_pct": max_delta, "optimization_id": opt_run.id}
