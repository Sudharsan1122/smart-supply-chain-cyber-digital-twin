"""Extra repos - blast radius, snapshots, attack story events."""
from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m


def utcnow(): return datetime.now(timezone.utc)


class BlastRadiusRepo:
    def __init__(self, session): self.session = session

    async def insert(self, source_asset_db_id, impacted_asset_db_id,
                     attack_story_db_id=None, depth=1, impact_score=None, path=None):
        obj = m.BlastRadius(
            attack_story_id=attack_story_db_id, source_asset_id=source_asset_db_id,
            impacted_asset_id=impacted_asset_db_id, depth=depth,
            impact_score=impact_score, path=path or [], computed_at=utcnow(),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def clear_for_story(self, story_id):
        await self.session.execute(delete(m.BlastRadius).where(m.BlastRadius.attack_story_id == story_id))
        await self.session.flush()

    async def list_for_story(self, story_id, limit=500):
        stmt = (select(m.BlastRadius).where(m.BlastRadius.attack_story_id == story_id)
                .order_by(m.BlastRadius.depth.asc(), m.BlastRadius.impact_score.desc()).limit(limit))
        return (await self.session.execute(stmt)).scalars().all()


class IOCEnrichmentRepo:
    def __init__(self, session): self.session = session

    async def insert(self, ioc_db_id, provider, verdict=None, raw=None):
        obj = m.IOCEnrichment(ioc_id=ioc_db_id, provider=provider, verdict=verdict,
                              raw=raw or {}, enriched_at=utcnow())
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_for_ioc(self, ioc_db_id, limit=200):
        stmt = (select(m.IOCEnrichment).where(m.IOCEnrichment.ioc_id == ioc_db_id)
                .order_by(m.IOCEnrichment.enriched_at.desc()).limit(limit))
        return (await self.session.execute(stmt)).scalars().all()


class AttackStoryEventRepo:
    def __init__(self, session): self.session = session

    async def add(self, story_db_id, evidence_kind, title, occurred_at, **kwargs):
        obj = m.AttackStoryEvent(
            story_id=story_db_id, evidence_kind=evidence_kind, title=title,
            occurred_at=occurred_at, evidence_id=kwargs.get("evidence_id"),
            asset_id=kwargs.get("asset_db_id"), severity=kwargs.get("severity"),
            details=kwargs.get("details") or {}, tactic=kwargs.get("tactic"),
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_for_story(self, story_db_id, limit=1000):
        stmt = (select(m.AttackStoryEvent).where(m.AttackStoryEvent.story_id == story_db_id)
                .order_by(m.AttackStoryEvent.occurred_at.asc()).limit(limit))
        return (await self.session.execute(stmt)).scalars().all()


class AttackStoryTacticRepo:
    def __init__(self, session): self.session = session

    async def upsert(self, story_db_id, tactic, confidence=None, evidence_count=0, notes=None):
        stmt = select(m.AttackStoryTactic).where(
            m.AttackStoryTactic.story_id == story_db_id,
            m.AttackStoryTactic.tactic == tactic,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.confidence = confidence
            existing.evidence_count = evidence_count
            existing.notes = notes
        else:
            self.session.add(m.AttackStoryTactic(
                story_id=story_db_id, tactic=tactic, confidence=confidence,
                evidence_count=evidence_count, notes=notes,
            ))
        await self.session.flush()

    async def list_for_story(self, story_db_id):
        stmt = (select(m.AttackStoryTactic).where(m.AttackStoryTactic.story_id == story_db_id)
                .order_by(m.AttackStoryTactic.evidence_count.desc()))
        return (await self.session.execute(stmt)).scalars().all()


class IOCObservationRepo:
    def __init__(self, session):
        self.session = session

    async def upsert(self, ioc_db_id, evidence_kind, asset_db_id=None,
                     attack_story_db_id=None, evidence_id=None, context=None):
        stmt = select(m.IOCObservation).where(
            m.IOCObservation.ioc_id == ioc_db_id,
            m.IOCObservation.evidence_kind == evidence_kind,
        )
        if asset_db_id is not None:
            stmt = stmt.where(m.IOCObservation.asset_id == asset_db_id)
        if attack_story_db_id is not None:
            stmt = stmt.where(m.IOCObservation.attack_story_id == attack_story_db_id)

        existing = (await self.session.execute(stmt)).scalars().first()
        if existing:
            existing.occurrences += 1
            existing.last_seen = utcnow()
            await self.session.flush()
            return existing
        obj = m.IOCObservation(
            ioc_id=ioc_db_id,
            asset_id=asset_db_id,
            attack_story_id=attack_story_db_id,
            evidence_kind=evidence_kind,
            evidence_id=evidence_id,
            context=context or {},
            first_seen=utcnow(),
            last_seen=utcnow(),
            occurrences=1,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_for_ioc(self, ioc_db_id, limit=200):
        stmt = (select(m.IOCObservation).where(m.IOCObservation.ioc_id == ioc_db_id)
                .order_by(m.IOCObservation.last_seen.desc()).limit(limit))
        return (await self.session.execute(stmt)).scalars().all()


from database import repository
if hasattr(repository, "Repository") and not hasattr(repository.Repository, "_ioc_obs_patched"):
    _orig_init = repository.Repository.__init__
    def _patched_init(self, session):
        _orig_init(self, session)
        self.ioc_observations = IOCObservationRepo(session)
    repository.Repository.__init__ = _patched_init
    repository.Repository._ioc_obs_patched = True

