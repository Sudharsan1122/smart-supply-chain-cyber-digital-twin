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
