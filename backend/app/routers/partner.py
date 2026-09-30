"""Partner-scoped API endpoints enforcing org_id isolation, k-anonymity, and HMAC-signed commitments (CR-001)."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.constants import PartnerConstants
from app.database import get_db
from app.exceptions import CommitmentReplayError, InvalidCommitmentError
from app.schemas import CommitmentCreate, CommitmentResponse, PartnerForecastResponse
from app.security import AuthenticatedUser, get_current_user, get_partner_context
from app.services.audit_service import PARTNER_ACCESS_DENIED, event_bus
from app.services.partner_service import PartnerService

router = APIRouter(tags=["partner"])


def _enforce_org_match(
    db: Session,
    requested_org_id: int | None,
    ctx: dict[str, Any],
    user: AuthenticatedUser,
) -> int:
    """Verify partner user is only accessing their own org_id, logging PARTNER_ACCESS_DENIED on mismatch."""
    if user.role != PartnerConstants.ROLE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only PARTNER role permitted")
    scoped_org_id = int(ctx["org_id"])
    if requested_org_id is not None and int(requested_org_id) != scoped_org_id:
        event_bus.publish(
            db,
            {
                "actor": user.sub,
                "action": PARTNER_ACCESS_DENIED,
                "resource": f"org:{requested_org_id}",
                "details": {
                    "ScopedOrg": scoped_org_id,
                    "RequestedOrg": requested_org_id,
                    "role": PartnerConstants.ROLE,
                },
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-organization access denied: org_id mismatch",
        )
    return scoped_org_id


@router.get("/forecast", response_model=PartnerForecastResponse)
def get_partner_forecast_endpoint(
    org_id: int | None = Query(default=None),
    region: str | None = Query(default=None),
    period: str = Query(default=PartnerConstants.DEFAULT_PERIOD),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
) -> PartnerForecastResponse:
    """Return k-anonymized (k>=5) regional demand forecast scoped to the partner's organization."""
    scoped_org_id = _enforce_org_match(db, org_id, ctx, user)
    target_region = region or str(ctx.get("region", PartnerConstants.DEFAULT_REGION))
    svc = PartnerService(db)
    try:
        data = svc.get_partner_forecast(org_id=scoped_org_id, region=target_region, period=period)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return PartnerForecastResponse(**data)


@router.post("/commit", response_model=CommitmentResponse, status_code=status.HTTP_201_CREATED)
def create_partner_commitment_endpoint(
    payload: CommitmentCreate,
    org_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
) -> CommitmentResponse:
    """Create and HMAC-sign a weekly capacity commitment, rejecting duplicate nonces with 409."""
    scoped_org_id = _enforce_org_match(db, org_id, ctx, user)
    svc = PartnerService(db)
    try:
        commitment = svc.create_commitment(org_id=scoped_org_id, payload=payload)
    except CommitmentReplayError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InvalidCommitmentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CommitmentResponse.model_validate(commitment)


@router.get("/commitments", response_model=list[CommitmentResponse])
def list_partner_commitments_endpoint(
    org_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
) -> list[CommitmentResponse]:
    """List weekly capacity commitments scoped strictly to the authenticated partner's org_id."""
    scoped_org_id = _enforce_org_match(db, org_id, ctx, user)
    svc = PartnerService(db)
    records = svc.list_commitments(org_id=scoped_org_id)
    return [CommitmentResponse.model_validate(r) for r in records]
