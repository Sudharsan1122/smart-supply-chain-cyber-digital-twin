"""Telemetry ingestion endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.telemetry import TelemetryPayload, TelemetryResponse
from database.db import get_db
from database.repository import Repository
from digital_twin.graph import twin_graph
from ingestion.pipeline import ingest_telemetry

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", response_model=TelemetryResponse, status_code=201)
async def post_telemetry(payload: TelemetryPayload, session: AsyncSession = Depends(get_db)):
    try:
        result = await ingest_telemetry(session, payload)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    return TelemetryResponse(
        success=True,
        telemetry_id=result["telemetry_ids"][0] if result["telemetry_ids"] else None,
        asset_id=payload.asset_id,
        timestamp=payload.timestamp,
        message=f"Persisted {result['row_count']} metric row(s)",
        twin_state=result["twin_state"],
    )


@router.get("/{asset_id}")
async def get_history(
    asset_id: str,
    metric: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db),
):
    if not twin_graph.has_node(asset_id):
        raise HTTPException(404, f"Unknown asset_id '{asset_id}'")
    db_id = twin_graph.db_id_for(asset_id)
    repo = Repository(session)
    rows = await repo.telemetry.latest_for_asset(db_id, metric=metric, limit=limit)
    return [
        {
            "id": r.id, "metric": r.metric, "value": r.value,
            "unit": r.unit, "source": r.source,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in rows
    ]
