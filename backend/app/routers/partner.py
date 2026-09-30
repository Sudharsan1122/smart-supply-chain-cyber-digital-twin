from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.constants import PartnerConstants
from app.database import get_db
from app.exceptions import PartnerKAnonymityError, PartnerNotFoundError, PartnerReplayError
from app.models import PartnerOrganization
from app.schemas import CommitmentCreate, CommitmentResponse
from app.security import AuthenticatedUser, get_current_user, get_partner_context
from app.services.audit_service import PARTNER_ACCESS_DENIED, log_event
from app.services.partner_service import PartnerService

router = APIRouter()


def _verify_org_access(
    db: Session,
    requested_org_id: str | None,
    ctx: dict[str, Any],
    user: AuthenticatedUser,
) -> str:
    if user.role != PartnerConstants.ROLE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Partner access only")
    scoped_org = str(ctx["org_id"])
    if requested_org_id is not None and str(requested_org_id) != scoped_org:
        log_event(
            db,
            PARTNER_ACCESS_DENIED,
            {"org_id": scoped_org, "requested_org_id": requested_org_id, "role": PartnerConstants.ROLE},
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-organization access denied: org_id mismatch")
    return scoped_org


@router.get("/forecast")
def get_forecast(
    org_id: str | None = Query(default=None),
    region: str | None = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scoped_org = _verify_org_access(db, org_id, ctx, user)
    svc = PartnerService(db)
    target_region = region or str(ctx["region"])
    try:
        return svc.get_partner_forecast(scoped_org, target_region)
    except (PartnerKAnonymityError, PartnerNotFoundError) as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e)) from e


@router.post("/commit", response_model=CommitmentResponse, status_code=status.HTTP_201_CREATED)
def submit_commitment(
    payload: CommitmentCreate,
    org_id: str | None = Query(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    ctx: dict[str, Any] = Depends(get_partner_context),
    db: Session = Depends(get_db),
) -> Any:
    scoped_org = _verify_org_access(db, org_id, ctx, user)
    svc = PartnerService(db)
    try:
        return svc.create_commitment(org_id=scoped_org, payload=payload)
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
    scoped_org = _verify_org_access(db, org_id, ctx, user)
    svc = PartnerService(db)
    partner = svc.db.query(PartnerOrganization).filter_by(org_id=scoped_org).first()
    if not partner:
        return []
    return list(partner.commitments)
