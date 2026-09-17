"""Repository pattern data access."""
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseRepository:
    model: type

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, obj_id: int):
        return await self.session.get(self.model, obj_id)

    async def list(self, stmt: Select | None = None, limit: int = 100) -> Sequence:
        stmt = stmt or select(self.model)
        return (await self.session.execute(stmt.limit(limit))).scalars().all()

    async def add(self, obj):
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete_by_id(self, obj_id: int) -> bool:
        obj = await self.get(obj_id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True


class AssetRepository(BaseRepository):
    model = m.Asset

    async def get_by_asset_id(self, asset_id: str) -> m.Asset | None:
        stmt = select(m.Asset).where(m.Asset.asset_id == asset_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_by_type(self, asset_type: str, limit: int = 100):
        stmt = select(m.Asset).where(m.Asset.asset_type == asset_type).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()


class TelemetryRepository(BaseRepository):
    model = m.Telemetry

    async def insert(self, asset_db_id: int, metric: str, value=None, unit=None,
                     source=None, payload=None, timestamp=None):
        obj = m.Telemetry(
            asset_id=asset_db_id, metric=metric, value=value, unit=unit,
            source=source, payload=payload or {},
            timestamp=timestamp or utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def latest_for_asset(self, asset_db_id: int, metric: str | None = None, limit: int = 100):
        stmt = (select(m.Telemetry)
                .where(m.Telemetry.asset_id == asset_db_id)
                .order_by(m.Telemetry.timestamp.desc()).limit(limit))
        if metric:
            stmt = stmt.where(m.Telemetry.metric == metric)
        return (await self.session.execute(stmt)).scalars().all()


class SecurityEventRepository(BaseRepository):
    model = m.SecurityEvent

    async def insert(self, asset_db_id: int, event_type: str, severity: str = "info",
                     description=None, source=None, payload=None, timestamp=None):
        obj = m.SecurityEvent(
            asset_id=asset_db_id, event_type=event_type, severity=severity,
            description=description, source=source, payload=payload or {},
            timestamp=timestamp or utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_by_severity(self, severity: str, limit: int = 100):
        stmt = (select(m.SecurityEvent)
                .where(m.SecurityEvent.severity == severity)
                .order_by(m.SecurityEvent.timestamp.desc()).limit(limit))
        return (await self.session.execute(stmt)).scalars().all()


class TwinStateRepository(BaseRepository):
    model = m.TwinState

    async def upsert(self, asset_db_id: int, state: str, health: str = "unknown",
                     position=None, metrics=None, last_seen=None):
        tbl = m.TwinState.__table__
        stmt = pg_insert(m.TwinState).values(
            asset_id=asset_db_id, state=state, health=health,
            position=position or {}, metrics=metrics or {},
            last_seen=last_seen or utcnow(),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[tbl.c.asset_id],
            set_={"state": stmt.excluded.state, "health": stmt.excluded.health,
                  "position": stmt.excluded.position, "metrics": stmt.excluded.metrics,
                  "last_seen": stmt.excluded.last_seen, "updated_at": utcnow()},
        ).returning(m.TwinState)
        return (await self.session.execute(stmt)).scalar_one()


class StateTransitionRepository(BaseRepository):
    model = m.StateTransition

    async def record(self, asset_db_id: int, to_state: str, from_state=None, reason=None):
        obj = m.StateTransition(
            asset_id=asset_db_id, from_state=from_state, to_state=to_state,
            reason=reason, transitioned_at=utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj


class DetectionRepository(BaseRepository):
    model = m.Detection

    async def insert(self, asset_db_id: int, detection_type: str, telemetry_db_id=None,
                     rule_id=None, model_version=None, confidence=None,
                     severity="medium", description=None):
        obj = m.Detection(
            asset_id=asset_db_id, detection_type=detection_type,
            telemetry_id=telemetry_db_id, rule_id=rule_id,
            model_version=model_version, confidence=confidence,
            severity=severity, description=description, detected_at=utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj


class RiskScoreRepository(BaseRepository):
    model = m.RiskScore

    async def insert(self, asset_db_id: int, score: float, factors=None, model_version=None):
        obj = m.RiskScore(asset_id=asset_db_id, score=score, factors=factors or {},
                          model_version=model_version, scored_at=utcnow())
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def latest_for_asset(self, asset_db_id: int):
        stmt = (select(m.RiskScore).where(m.RiskScore.asset_id == asset_db_id)
                .order_by(m.RiskScore.scored_at.desc()).limit(1))
        return (await self.session.execute(stmt)).scalars().first()


class AttackScenarioRepository(BaseRepository):
    model = m.AttackScenario

    async def get_by_scenario_id(self, scenario_id: str):
        stmt = select(m.AttackScenario).where(m.AttackScenario.scenario_id == scenario_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()


class AttackStoryRepository(BaseRepository):
    model = m.AttackStory

    async def create(self, title: str, attack_id=None, scenario_db_id=None,
                     narrative=None, status="open"):
        import uuid
        obj = m.AttackStory(
            attack_id=attack_id or str(uuid.uuid4()),
            scenario_id=scenario_db_id, title=title, narrative=narrative,
            status=status, started_at=utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_attack_id(self, attack_id: str):
        stmt = select(m.AttackStory).where(m.AttackStory.attack_id == attack_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()


class IOCRepository(BaseRepository):
    model = m.IOC

    async def upsert(self, value: str, ioc_type: str, source=None, confidence=None):
        tbl = m.IOC.__table__
        stmt = pg_insert(m.IOC).values(
            value=value, ioc_type=ioc_type, source=source, confidence=confidence,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[tbl.c.value, tbl.c.ioc_type],
            set_={"last_seen": utcnow(), "confidence": stmt.excluded.confidence},
        ).returning(m.IOC)
        return (await self.session.execute(stmt)).scalar_one()

    async def list_all(self, limit: int = 500):
        stmt = select(m.IOC).order_by(m.IOC.last_seen.desc()).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()


class TriageRepository(BaseRepository):
    model = m.Triage

    async def classify(self, detection_db_id: int, verdict: str, confidence=None,
                       analyst=None, notes=None):
        obj = m.Triage(
            detection_id=detection_db_id, verdict=verdict, confidence=confidence,
            analyst=analyst, notes=notes, created_at=utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj


class IncidentRepository(BaseRepository):
    model = m.Incident

    async def create(self, incident_uid: str, title: str, rule_id: str,
                     window_start, window_end, root_asset_db_id=None,
                     severity="medium", confidence=None, description=None, metadata_=None):
        obj = m.Incident(
            incident_uid=incident_uid, title=title, rule_id=rule_id,
            window_start=window_start, window_end=window_end,
            root_asset_id=root_asset_db_id, severity=severity,
            confidence=confidence, description=description,
            metadata_=metadata_ or {},
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_uid(self, incident_uid: str):
        stmt = select(m.Incident).where(m.Incident.incident_uid == incident_uid)
        return (await self.session.execute(stmt)).scalar_one_or_none()


class IncidentMemberRepository(BaseRepository):
    model = m.IncidentMember

    async def add_telemetry(self, incident_db_id: int, telemetry_db_id: int, role: str = "evidence"):
        obj = m.IncidentMember(incident_id=incident_db_id, telemetry_id=telemetry_db_id, role=role)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def add_event(self, incident_db_id: int, event_db_id: int, role: str = "evidence"):
        obj = m.IncidentMember(incident_id=incident_db_id, event_id=event_db_id, role=role)
        self.session.add(obj)
        await self.session.flush()
        return obj


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.assets = AssetRepository(session)
        self.telemetry = TelemetryRepository(session)
        self.security_events = SecurityEventRepository(session)
        self.twin_states = TwinStateRepository(session)
        self.state_transitions = StateTransitionRepository(session)
        self.detections = DetectionRepository(session)
        self.risk_scores = RiskScoreRepository(session)
        self.attack_scenarios = AttackScenarioRepository(session)
        self.attack_stories = AttackStoryRepository(session)
        self.iocs = IOCRepository(session)
        self.triage = TriageRepository(session)
        self.incidents = IncidentRepository(session)
        self.incident_members = IncidentMemberRepository(session)
        from database.repository_extra import (
            BlastRadiusRepo, IOCEnrichmentRepo,
            AttackStoryEventRepo, AttackStoryTacticRepo,
        )
        self.blast_radius = BlastRadiusRepo(session)
        self.ioc_enrichments = IOCEnrichmentRepo(session)
        self.attack_story_events = AttackStoryEventRepo(session)
        self.attack_story_tactics = AttackStoryTacticRepo(session)
