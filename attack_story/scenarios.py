"""Phase 13 - Scenario loader."""
from dataclasses import dataclass
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m


@dataclass
class Scenario:
    scenario_id: str
    name: str
    description: str
    target_asset_types: list[str]
    params: dict[str, Any]

    @property
    def tick_seconds(self) -> int:
        return int(self.params.get("tick_seconds", 2))

    @property
    def default_assets(self) -> list[str]:
        return list(self.params.get("assets", []))

    @property
    def metrics(self) -> dict:
        return dict(self.params.get("metrics", {}))

    @property
    def final_event(self):
        return self.params.get("final_event")


async def load_all(session: AsyncSession) -> dict[str, Scenario]:
    stmt = select(m.AttackScenario).order_by(m.AttackScenario.scenario_id)
    rows = (await session.execute(stmt)).scalars().all()
    return {r.scenario_id: Scenario(
        scenario_id=r.scenario_id, name=r.name, description=r.description or "",
        target_asset_types=list(r.target_asset_types or []), params=dict(r.params or {}),
    ) for r in rows}


async def load_one(session: AsyncSession, scenario_id: str) -> Scenario | None:
    stmt = select(m.AttackScenario).where(m.AttackScenario.scenario_id == scenario_id)
    r = (await session.execute(stmt)).scalar_one_or_none()
    if r is None:
        return None
    return Scenario(scenario_id=r.scenario_id, name=r.name,
                    description=r.description or "",
                    target_asset_types=list(r.target_asset_types or []),
                    params=dict(r.params or {}))
