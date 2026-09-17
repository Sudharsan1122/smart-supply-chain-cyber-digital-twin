"""Event ingestion."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas.events import EventPayload, EventResponse
from database.db import get_db
from database.repository import Repository
from digital_twin.graph import twin_graph
from ingestion.pipeline import ingest_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=201)
async def post_event(payload: EventPayload, session: AsyncSession = Depends(get_db)):
    result = await ingest_event(session, payload)
    return EventResponse(success=True, event_id=result["event_id"],
                         asset_id=payload.asset_id, event_type=payload.event_type,
                         severity=payload.severity, timestamp=payload.timestamp,
                         message="Event persisted")


@router.get("")
async def list_events(severity: str | None = Query(None), limit: int = Query(100, ge=1, le=1000),
                      session: AsyncSession = Depends(get_db)):
    repo = Repository(session)
    if severity:
        rows = await repo.security_events.list_by_severity(severity, limit=limit)
    else:
        rows = await repo.security_events.list(limit=limit)
    return [{"id": r.id, "asset_id": r.asset_id, "event_type": r.event_type,
             "severity": r.severity, "description": r.description,
             "timestamp": r.timestamp.isoformat()} for r in rows]
