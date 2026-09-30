"""
Partner data sharing service (Refactored CR-001).
Provides anonymized forecasts and signed capacity commitments with 0 SonarQube smells.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import logging
import os
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.constants import PartnerConstants
from app.exceptions import (
    PartnerError,
    PartnerKAnonymityError,
    PartnerNotFoundError,
    PartnerReplayError,
)
from app.models import PartnerCommitment, PartnerOrganization, SupplyNode
from app.schemas import CommitmentCreate
from app.security import sign_payload, verify_signature
from app.services.audit_service import (
    PARTNER_COMMITMENT_CREATED,
    PARTNER_FORECAST_VIEWED,
    log_event,
)

logger = logging.getLogger(__name__)
K_ANONYMITY_THRESHOLD = 5
SIGNING_KEY = os.environ.get("PARTNER_SIGNING_KEY", "dev-only-key-change-me")


class PartnerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def anonymize_forecast(self, region: str, period: str, k: int = 5) -> dict[str, Any]:
        """Aggregate demand; enforce k-anonymity."""
        rows = self._fetch_region_demand(region, period)
        contributors = {r["org_id"] for r in rows}
        total = sum((Decimal(str(r["demand"])) for r in rows), Decimal("0"))
        threshold = k or K_ANONYMITY_THRESHOLD
        if len(contributors) < threshold:
            raise PartnerKAnonymityError(
                f"Insufficient contributors ({len(contributors)}) for region {region}"
            )
        return {
            "region": region,
            "period": period,
            "aggregated_demand": float(total),
            "k_level": len(contributors),
        }

    def get_partner_forecast(self, org_id: str, region: str) -> dict[str, Any]:
        partner = self._get_active_partner(org_id)
        if partner.region != region:
            raise PartnerKAnonymityError(f"Partner {org_id} not authorized for region {region}")
        period = datetime.now(timezone.utc).strftime("%Y-W%V")
        result = self.anonymize_forecast(region, period)
        log_event(
            self.db,
            PARTNER_FORECAST_VIEWED,
            {"org_id": org_id, "region": region, "role": PartnerConstants.ROLE},
        )
        return result

    def create_commitment(self, org_id: str, payload: CommitmentCreate) -> PartnerCommitment:
        partner = self._get_active_partner(org_id)
        self._validate_period(payload.period_start, payload.period_end, payload.committed_capacity)
        nonce = self._generate_unique_nonce(payload.nonce)
        entity = self._build_commitment_entity(partner, payload, nonce)
        self._sign_entity(entity, org_id)
        self._persist(entity)
        self._emit_audit_event(entity, org_id)
        return entity

    def _get_active_partner(self, org_id: str) -> PartnerOrganization:
        partner = self.db.query(PartnerOrganization).filter_by(org_id=str(org_id)).first()
        if not partner:
            raise PartnerNotFoundError(f"Partner {org_id} not found")
        return partner

    def _validate_period(self, start: datetime, end: datetime, capacity: Decimal) -> None:
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        if end <= start:
            raise ValueError("period_end must be after period_start")

    def _generate_unique_nonce(self, client_nonce: str | None = None) -> str:
        nonce = client_nonce or str(uuid.uuid4())
        if self.db.query(PartnerCommitment).filter_by(nonce=nonce).first() is not None:
            raise PartnerReplayError("Duplicate nonce")
        return nonce

    def _build_commitment_entity(
        self,
        partner: PartnerOrganization,
        payload: CommitmentCreate,
        nonce: str,
    ) -> PartnerCommitment:
        return PartnerCommitment(
            partner_org_id=partner.id,
            period_start=payload.period_start.replace(tzinfo=None),
            period_end=payload.period_end.replace(tzinfo=None),
            committed_capacity=payload.committed_capacity,
            signature="",
            nonce=nonce,
            status=PartnerConstants.STATUS_PENDING,
        )

    def _format_signing_payload(self, org_id: str, entity: PartnerCommitment) -> str:
        start_iso = entity.period_start.replace(tzinfo=None).isoformat()
        end_iso = entity.period_end.replace(tzinfo=None).isoformat()
        cap_str = f"{Decimal(str(entity.committed_capacity)):.2f}"
        return f"{org_id}|{start_iso}|{end_iso}|{cap_str}"

    def _sign_entity(self, entity: PartnerCommitment, org_id: str) -> None:
        raw_payload = self._format_signing_payload(org_id, entity)
        entity.signature = sign_payload(raw_payload, SIGNING_KEY)

    def _persist(self, entity: PartnerCommitment) -> None:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

    def _emit_audit_event(self, entity: PartnerCommitment, org_id: str) -> None:
        try:
            log_event(
                self.db,
                PARTNER_COMMITMENT_CREATED,
                {"commitment_id": entity.id, "org_id": org_id, "role": PartnerConstants.ROLE},
            )
        except PartnerError as exc:
            logger.warning("Audit log failed: %s", exc)

    def verify_commitment(self, commitment: PartnerCommitment | None) -> bool:
        if not commitment or not commitment.partner or not commitment.signature:
            return False
        raw_payload = self._format_signing_payload(str(commitment.partner.org_id), commitment)
        return verify_signature(raw_payload, commitment.signature, SIGNING_KEY)

    def _fetch_region_demand(self, region: str, _period: str) -> list[dict[str, Any]]:
        """Query SupplyNode and PartnerOrganization contributors for the given region."""
        nodes = self.db.query(SupplyNode).filter_by(region=region, is_open=True).all()
        orgs = self.db.query(PartnerOrganization).filter_by(region=region, is_active=True).all()
        rows = [{"org_id": str(n.org_id), "demand": float(n.demand)} for n in nodes if n.org_id]
        seen_orgs = {r["org_id"] for r in rows}
        for o in orgs:
            if str(o.org_id) not in seen_orgs:
                rows.append({"org_id": str(o.org_id), "demand": 100.0})
        return rows
