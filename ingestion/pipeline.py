"""Phase 5+6+7+10+12 - Ingestion pipeline."""
from __future__ import annotations
import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.events import EventPayload
from api.schemas.telemetry import TelemetryPayload
from database.repository import Repository
from detection.engine import run_detection
from detection.risk import score_asset
from digital_twin.graph import twin_graph
from digital_twin.state_manager import twin_state
from ingestion.correlator import correlate
from ingestion.normalizer import derive_twin_state, to_metric_rows
from ingestion.validators import validate
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


async def ingest_telemetry(session: AsyncSession, payload: TelemetryPayload,
                           run_correlation=True, run_detections=True, run_risk=True) -> dict[str, Any]:
    if not twin_graph.has_node(payload.asset_id):
        raise HTTPException(404, f"Unknown asset_id '{payload.asset_id}'")

    vr = validate(payload)
    if not vr.ok:
        raise HTTPException(422, detail={"validation_errors": vr.reasons})

    db_id = twin_graph.db_id_for(payload.asset_id)
    if db_id is None:
        raise HTTPException(500, "Twin graph missing DB id")

    repo = Repository(session)
    rows = to_metric_rows(payload)
    ts = payload.timestamp or _now()
    inserted_ids = []
    for r in rows:
        extra = dict(r.get("payload") or {})
        if vr.flags:
            extra["_flags"] = vr.flags
        t = await repo.telemetry.insert(
            asset_db_id=db_id, metric=r["metric"], value=r.get("value"),
            unit=r.get("unit"), source=(payload.raw or {}).get("source", "api"),
            payload=extra, timestamp=ts,
        )
        inserted_ids.append(t.id)

    derived = derive_twin_state(payload)
    await repo.twin_states.upsert(
        asset_db_id=db_id, state=derived["state"], health=derived["health"],
        position=derived["position"], metrics=derived["metrics"], last_seen=ts,
    )
    await twin_state.update_state(
        session, payload.asset_id,
        state=derived["state"], health=derived["health"],
        position=derived["position"], metrics=derived["metrics"],
    )

    incidents_created = []
    if run_correlation:
        for c in await correlate(session, payload.asset_id):
            if await repo.incidents.get_by_uid(c.uid):
                continue
            inc = await repo.incidents.create(
                incident_uid=c.uid, title=c.title, rule_id=c.rule_id,
                window_start=c.window_start, window_end=c.window_end,
                root_asset_db_id=db_id, severity=c.severity,
                confidence=c.confidence, description=c.description,
                metadata_=c.metadata,
            )
            for tid in c.telemetry_ids:
                await repo.incident_members.add_telemetry(inc.id, tid)
            for eid in c.event_ids:
                await repo.incident_members.add_event(inc.id, eid)
            incidents_created.append(c.uid)

    detections = []
    if run_detections:
        detections = await run_detection(session, payload, validation_flags=vr.flags)

    risk = None
    if run_risk:
        risk = await score_asset(session, payload.asset_id, persist=True)

    await session.commit()
    return {
        "telemetry_ids": inserted_ids, "row_count": len(inserted_ids),
        "twin_state": twin_state.get(payload.asset_id),
        "validation_flags": vr.flags,
        "incidents_created": incidents_created, "detections": detections, "risk": risk,
    }


async def ingest_event(session: AsyncSession, payload: EventPayload,
                       run_correlation=True, run_detections=True, run_risk=True) -> dict[str, Any]:
    if not twin_graph.has_node(payload.asset_id):
        raise HTTPException(404, f"Unknown asset_id '{payload.asset_id}'")
    db_id = twin_graph.db_id_for(payload.asset_id)
    if db_id is None:
        raise HTTPException(500, "Twin graph missing DB id")

    repo = Repository(session)
    ev = await repo.security_events.insert(
        asset_db_id=db_id, event_type=payload.event_type, severity=payload.severity,
        description=payload.description, source=payload.source or "api",
        payload=payload.payload, timestamp=payload.timestamp or _now(),
    )

    detections = []
    if run_detections:
        detections = await run_detection(session, payload)

    await session.commit()
    return {"event_id": ev.id, "incidents_created": [], "detections": detections}
