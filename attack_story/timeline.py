"""Phase 14 - Timeline reconstruction."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from attack_story.tactics import (tactic_for_detection, tactic_for_event,
                                   tactic_for_incident, tactic_for_transition)
from database import models as m

logger = logging.getLogger(__name__)


@dataclass
class TimelineEntry:
    evidence_kind: str
    evidence_id: int | None
    occurred_at: Any
    asset_db_id: int | None
    severity: str | None
    title: str
    details: dict = field(default_factory=dict)
    tactic: str | None = None


def _story_window(story, padding_seconds=30):
    start = story.started_at or story.created_at
    end = story.ended_at or story.created_at
    return (start - timedelta(seconds=padding_seconds),
            end + timedelta(seconds=padding_seconds))


async def build_timeline(session: AsyncSession, story, asset_db_ids: list[int]):
    start, end = _story_window(story)
    entries: list[TimelineEntry] = []

    if asset_db_ids:
        stmt_t = (select(m.Telemetry).where(m.Telemetry.asset_id.in_(asset_db_ids))
                  .where(m.Telemetry.timestamp >= start)
                  .where(m.Telemetry.timestamp <= end))
        for t in (await session.execute(stmt_t)).scalars().all():
            flags = (t.payload or {}).get("_flags") or []
            if not flags:
                continue
            entries.append(TimelineEntry(
                "telemetry", t.id, t.timestamp, t.asset_id, "medium",
                f"{t.metric}={t.value} {t.unit or ''}".strip(),
                {"metric": t.metric, "value": t.value, "flags": flags},
            ))

        stmt_e = (select(m.SecurityEvent).where(m.SecurityEvent.asset_id.in_(asset_db_ids))
                  .where(m.SecurityEvent.timestamp >= start)
                  .where(m.SecurityEvent.timestamp <= end))
        for e in (await session.execute(stmt_e)).scalars().all():
            entries.append(TimelineEntry(
                "event", e.id, e.timestamp, e.asset_id, e.severity,
                e.event_type,
                {"description": e.description, "payload": e.payload or {}},
                tactic=tactic_for_event(e.event_type),
            ))

        stmt_d = (select(m.Detection).where(m.Detection.asset_id.in_(asset_db_ids))
                  .where(m.Detection.detected_at >= start)
                  .where(m.Detection.detected_at <= end))
        for d in (await session.execute(stmt_d)).scalars().all():
            entries.append(TimelineEntry(
                "detection", d.id, d.detected_at, d.asset_id, d.severity,
                f"{d.rule_id or 'ML'}: {d.description or ''}".strip(),
                {"rule_id": d.rule_id, "confidence": d.confidence},
                tactic=tactic_for_detection(d.rule_id),
            ))

        stmt_tr = (select(m.TransitionAnomaly)
                   .where(m.TransitionAnomaly.asset_id.in_(asset_db_ids))
                   .where(m.TransitionAnomaly.detected_at >= start)
                   .where(m.TransitionAnomaly.detected_at <= end))
        for a in (await session.execute(stmt_tr)).scalars().all():
            entries.append(TimelineEntry(
                "transition", a.id, a.detected_at, a.asset_id, a.severity,
                f"Invalid: {a.from_state} -> {a.to_state}",
                {"machine": a.machine, "reason": a.reason, "kind": a.kind},
                tactic=tactic_for_transition(a.from_state, a.to_state),
            ))

        stmt_i = (select(m.Incident)
                  .where(m.Incident.root_asset_id.in_(asset_db_ids))
                  .where(m.Incident.window_start >= start)
                  .where(m.Incident.window_start <= end))
        for i in (await session.execute(stmt_i)).scalars().all():
            entries.append(TimelineEntry(
                "incident", i.id, i.window_start, i.root_asset_id, i.severity,
                f"{i.rule_id}: {i.title}",
                {"rule_id": i.rule_id, "confidence": i.confidence},
                tactic=tactic_for_incident(i.rule_id),
            ))

    entries.sort(key=lambda e: e.occurred_at)
    return entries
