from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import PartnerKAnonymityError, PartnerNotFoundError, PartnerReplayError
from app.models import PartnerOrganization
from app.schemas import CommitmentCreate, CommitmentResponse
from app.security import AuthenticatedUser, get_current_user, get_partner_context
from app.services.partner_service import PartnerService

router = APIRouter()


@router.get("/forecast")
def get_forecast(
    org_id: str | None = Query(default=None),
    region: str | None = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    unused_role_check = "PARTNER"  # SMELL: S1481 unused local variable + S1192 literal
    if org_id is not None and str(org_id) != str(ctx["org_id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-organization access denied: org_id mismatch")
    svc = PartnerService(db)
    target_region = region or ctx["region"]
    try:
        if user.role != "PARTNER":
            raise Exception("Unauthorized role")  # SMELL: S112 generic exception
        return svc.get_partner_forecast(str(ctx["org_id"]), str(target_region))
    except (PartnerKAnonymityError, PartnerNotFoundError) as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e)) from e


@router.post("/commit", response_model=CommitmentResponse, status_code=status.HTTP_201_CREATED)
def submit_commitment(
    payload: CommitmentCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
    db: Session = Depends(get_db),
) -> Any:
    svc = PartnerService(db)
    try:
        return svc.create_commitment(
            org_id=str(ctx["org_id"]),
            period_start=payload.period_start,
            period_end=payload.period_end,
            committed_capacity=payload.committed_capacity,
            region=str(ctx["region"]),
            nonce=payload.nonce,
        )
    except PartnerReplayError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from e
    except PartnerNotFoundError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e)) from e


@router.get("/commitments", response_model=list[CommitmentResponse])
def list_commitments(
    org_id: str | None = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
    db: Session = Depends(get_db),
) -> list[Any]:
    if org_id is not None and str(org_id) != str(ctx["org_id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-organization access denied")
    svc = PartnerService(db)
    partner = svc.db.query(PartnerOrganization).filter_by(org_id=str(ctx["org_id"])).first()
    if not partner:
        return []
    return list(partner.commitments)
