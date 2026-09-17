"""Attack story endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import models as m
from database.db import get_db

router = APIRouter(prefix="/attack-stories", tags=["attack-stories"])


@router.get("")
async def list_stories(limit: int = Query(50, ge=1, le=500),
                      session: AsyncSession = Depends(get_db)):
    stmt = select(m.AttackStory).order_by(m.AttackStory.created_at.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": r.id, "attack_id": r.attack_id, "title": r.title,
             "status": r.status, "narrative": r.narrative,
             "started_at": r.started_at.isoformat() if r.started_at else None,
             "ended_at": r.ended_at.isoformat() if r.ended_at else None,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/{attack_id}")
async def get_story(attack_id: str, session: AsyncSession = Depends(get_db)):
    stmt = select(m.AttackStory).where(m.AttackStory.attack_id == attack_id)
    story = (await session.execute(stmt)).scalar_one_or_none()
    if story is None:
        raise HTTPException(404, "Story not found")
    events_stmt = (select(m.AttackStoryEvent).where(m.AttackStoryEvent.story_id == story.id)
                   .order_by(m.AttackStoryEvent.occurred_at.asc()))
    events = (await session.execute(events_stmt)).scalars().all()
    tactics_stmt = (select(m.AttackStoryTactic).where(m.AttackStoryTactic.story_id == story.id)
                    .order_by(m.AttackStoryTactic.evidence_count.desc()))
    tactics = (await session.execute(tactics_stmt)).scalars().all()
    return {
        "id": story.id, "attack_id": story.attack_id, "title": story.title,
        "narrative": story.narrative, "status": story.status,
        "started_at": story.started_at.isoformat() if story.started_at else None,
        "ended_at": story.ended_at.isoformat() if story.ended_at else None,
        "events": [{"id": e.id, "evidence_kind": e.evidence_kind, "title": e.title,
                    "occurred_at": e.occurred_at.isoformat(),
                    "severity": e.severity, "tactic": e.tactic,
                    "details": e.details} for e in events],
        "tactics": [{"tactic": t.tactic, "confidence": t.confidence,
                     "evidence_count": t.evidence_count} for t in tactics],
    }
