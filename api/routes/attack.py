"""Attack simulation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db
from digital_twin.graph import twin_graph

router = APIRouter(prefix="/attack-simulation", tags=["attack"])


@router.get("/scenarios")
async def list_scenarios(session: AsyncSession = Depends(get_db)):
    stmt = select(m.AttackScenario).order_by(m.AttackScenario.scenario_id)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"scenario_id": r.scenario_id, "name": r.name,
             "description": r.description,
             "target_asset_types": r.target_asset_types,
             "params": r.params} for r in rows]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(m.AttackScenario).where(m.AttackScenario.scenario_id == scenario_id)
    r = (await session.execute(stmt)).scalar_one_or_none()
    if r is None:
        raise HTTPException(404, "Scenario not found")
    return {"scenario_id": r.scenario_id, "name": r.name, "params": r.params}


@router.post("/start")
async def start_attack(payload: dict, session: AsyncSession = Depends(get_db)):
    scenario_id = payload.get("scenario")
    target = payload.get("target")
    if not scenario_id or not target:
        raise HTTPException(400, "scenario and target required")
    if not twin_graph.has_node(target):
        raise HTTPException(404, f"Unknown target '{target}'")

    from attack_story.runner import start_attack as run_attack
    from attack_story.scenarios import load_one
    scenario = await load_one(session, scenario_id)
    if scenario is None:
        raise HTTPException(404, f"Scenario '{scenario_id}' not found")

    result = await run_attack(
        scenario, target,
        duration_seconds=payload.get("duration_seconds", 20),
        intensity=payload.get("intensity", "medium"),
    )
    return result
