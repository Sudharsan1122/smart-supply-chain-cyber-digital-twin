"""Phase 13 - Attack runner."""
from __future__ import annotations
import asyncio, logging, uuid
from datetime import datetime, timezone
from typing import Any

from api.schemas.telemetry import TelemetryPayload
from database.db import AsyncSessionLocal
from database.repository import Repository
from digital_twin.graph import twin_graph
from ingestion.pipeline import ingest_telemetry

logger = logging.getLogger(__name__)
_ACTIVE_RUNS: dict[str, dict] = {}


def active_runs(): return dict(_ACTIVE_RUNS)
def get_run(run_id): return _ACTIVE_RUNS.get(run_id)


class AttackRunner:
    def __init__(self, scenario, target, duration, intensity, story_db_id, run_id):
        self.scenario = scenario
        self.target = target
        self.duration = duration
        self.intensity = intensity
        self.story_db_id = story_db_id
        self.run_id = run_id
        self._ticks = 0

    def _mul(self):
        return {"low": 0.5, "medium": 1.0, "high": 1.75}.get(self.intensity, 1.0)

    def _build(self):
        m = dict(self.scenario.metrics)
        mul = self._mul()
        for k in ("unusual_api_calls", "failed_logins", "auth_events"):
            if k in m and isinstance(m[k], (int, float)):
                m[k] = int(m[k] * mul)
        node = twin_graph.graph.nodes[self.target]
        return TelemetryPayload(
            asset_id=self.target,
            asset_type=node["asset_type"],
            status=m.pop("status", "ACTIVE"),
            firmware=m.pop("firmware", None),
            network_destinations=m.pop("network_destinations", []),
            temperature=m.pop("temperature", None),
            door_status=m.pop("door_status", None),
            failed_logins=m.pop("failed_logins", 0),
            unusual_api_calls=m.pop("unusual_api_calls", 0),
            auth_events=m.pop("auth_events", 0),
            occupancy=m.pop("occupancy", None),
            raw={"source": f"attack:{self.scenario.scenario_id}"},
        )

    async def _tick(self):
        async with AsyncSessionLocal() as session:
            try:
                await ingest_telemetry(session, self._build())
                self._ticks += 1
            except Exception as e:
                logger.warning("Attack tick failed: %s", e)

    async def run(self):
        try:
            end = asyncio.get_event_loop().time() + self.duration
            while asyncio.get_event_loop().time() < end:
                await self._tick()
                await asyncio.sleep(self.scenario.tick_seconds)
            await self._finalize("completed")
        except asyncio.CancelledError:
            await self._finalize("cancelled")
        except Exception as e:
            logger.exception("Attack error: %s", e)
            await self._finalize("failed")
        finally:
            _ACTIVE_RUNS.pop(self.run_id, None)

    async def _finalize(self, status):
        async with AsyncSessionLocal() as session:
            repo = Repository(session)
            story = await repo.attack_stories.get(self.story_db_id)
            if story:
                story.status = status
                story.ended_at = datetime.now(timezone.utc)
                story.narrative = f"Ran {self._ticks} ticks over {self.duration}s."
                await session.commit()
        try:
            from attack_story.story import build_story
            async with AsyncSessionLocal() as session:
                await build_story(session, self.story_db_id)
        except Exception as e:
            logger.exception("Story build failed: %s", e)


async def start_attack(scenario, target, duration_seconds=20, intensity="medium"):
    if not twin_graph.has_node(target):
        raise ValueError(f"Unknown target '{target}'")
    async with AsyncSessionLocal() as session:
        repo = Repository(session)
        sc_row = await repo.attack_scenarios.get_by_scenario_id(scenario.scenario_id)
        story = await repo.attack_stories.create(
            title=f"{scenario.name} -> {target}",
            attack_id=str(uuid.uuid4()),
            scenario_db_id=sc_row.id if sc_row else None,
            narrative=f"Attack started against {target}",
            status="running",
        )
        await session.commit()
        story_id, story_uid = story.id, story.attack_id

    run_id = str(uuid.uuid4())
    runner = AttackRunner(scenario, target, duration_seconds, intensity, story_id, run_id)
    _ACTIVE_RUNS[run_id] = {
        "run_id": run_id, "scenario_id": scenario.scenario_id,
        "scenario_name": scenario.name, "target": target,
        "intensity": intensity, "duration_seconds": duration_seconds,
        "attack_story_id": story_id, "attack_story_uid": story_uid,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    asyncio.create_task(runner.run())
    return {"run_id": run_id, "attack_story_uid": story_uid,
            "scenario_id": scenario.scenario_id, "target": target,
            "duration_seconds": duration_seconds, "intensity": intensity,
            "status": "running"}
