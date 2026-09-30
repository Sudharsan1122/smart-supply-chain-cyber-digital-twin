"""Audit log router exposing append-only signed audit trail and cryptographic chain verification."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AuditLogRead
from app.security import RoleEnum, get_current_principal, require_role
from app.services.audit_service import verify_audit_chain
from app.services.db_service import db_service
from app.services.notification_service import list_recent_notifications

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogRead])
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def get_audit_logs(
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> list[AuditLogRead]:
    """Return recent append-only signed audit records."""
    _ = principal
    rows = db_service.list_audit_logs(db, limit=100)
    return [AuditLogRead.model_validate(r) for r in rows]


@router.get("/verify")
@require_role(RoleEnum.ADMIN.value, RoleEnum.PLANNER.value)
def check_audit_integrity(
    db: Session = Depends(get_db),
    principal: dict[str, Any] = Depends(get_current_principal),
) -> dict[str, object]:
    """Verify the HMAC-SHA256 hash chain across all persisted audit records."""
    _ = principal
    valid = verify_audit_chain(db)
    return {"chain_valid": valid, "notifications": list_recent_notifications(limit=10)}
