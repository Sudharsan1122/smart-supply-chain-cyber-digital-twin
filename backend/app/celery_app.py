"""Celery distributed task queue configuration backed by Redis 7."""
from __future__ import annotations

import logging
from celery import Celery

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "scdt_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=settings.simulation_timeout_seconds,
    task_time_limit=settings.simulation_timeout_seconds + 5,
)


@celery_app.task(name="scdt.async_reoptimize")
def async_reoptimize_task(trigger_reason: str) -> dict[str, object]:
    """Execute background MILP re-optimization inside a Celery worker process.

    Args:
        trigger_reason: Description of the >5% drift event that triggered optimization.

    Returns:
        Summary dictionary of the completed optimization run.
    """
    from app.database import SessionLocal
    from app.optimization.solver import run_network_optimization
    from app.optimization.storage_interface import SqlAlchemyOptimizationStorage

    with SessionLocal() as session:
        storage = SqlAlchemyOptimizationStorage(session)
        result = run_network_optimization(storage, trigger_reason=trigger_reason, actor="SYSTEM_AUTO_TRIGGER")
        logger.info("Celery re-optimization complete: cost=%.2f", result.objective_cost)
        return {"id": result.id, "status": result.status, "objective_cost": result.objective_cost}
