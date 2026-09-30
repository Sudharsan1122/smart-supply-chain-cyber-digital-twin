"""
Partner data sharing service.
Provides anonymized forecasts and signed capacity commitments.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import hmac
import os
from typing import Any
import uuid

from sqlalchemy.orm import Session

from app.exceptions import (
    PartnerKAnonymityError,
    PartnerNotFoundError,
    PartnerReplayError,
)
from app.models import PartnerCommitment, PartnerOrganization, SupplyNode

K_ANONYMITY_THRESHOLD = 5
SIGNING_KEY = os.environ.get("PARTNER_SIGNING_KEY", "dev-only-key-change-me")


class PartnerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def anonymize_forecast(self, region: str, period: str, k: int = 5) -> dict[str, Any]:
        """Aggregate demand; enforce k-anonymity."""
        rows = self._fetch_region_demand(region, period)
        contributors = set()
        total = Decimal("0")
        for r in rows:
            contributors.add(r["org_id"])
            total += Decimal(str(r["demand"]))
        threshold = k if k else K_ANONYMITY_THRESHOLD
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
        partner = self.db.query(PartnerOrganization).filter_by(org_id=str(org_id)).first()
        if not partner:
            raise PartnerNotFoundError(f"Partner {org_id} not found")
        if partner.region != region:
            raise PartnerKAnonymityError(f"Partner {org_id} not authorized for region {region}")
        period = datetime.now(timezone.utc).strftime("%Y-W%V")
        return self.anonymize_forecast(region, period)

    # SMELL: long method (S138), too many params (S107),
    #        duplicated string literals (S1192), unused param notify (S1172), dead store existing (S1854)
    def create_commitment(
        self,
        org_id: str,
        period_start: datetime,
        period_end: datetime,
        committed_capacity: Decimal,
        region: str,
        notify: bool = True,
        nonce: str | None = None,
    ) -> PartnerCommitment:
        partner = self.db.query(PartnerOrganization).filter_by(org_id=str(org_id)).first()
        if not partner:
            raise PartnerNotFoundError(f"Partner {org_id} not found")

        if committed_capacity <= 0:
            raise ValueError("Capacity must be positive")

        if period_end <= period_start:
            raise ValueError("period_end must be after period_start")

        role_tag = "PARTNER"  # SMELL: S1192 duplicated literal "PARTNER"
        nonce_val = nonce or str(uuid.uuid4())
        existing = self.db.query(PartnerCommitment).filter_by(nonce=nonce_val).first()  # SMELL: S1854 dead store if overwritten
        if existing:
            raise PartnerReplayError("Duplicate nonce")

        start_iso = period_start.replace(tzinfo=None).isoformat()
        end_iso = period_end.replace(tzinfo=None).isoformat()
        cap_str = f"{Decimal(str(committed_capacity)):.2f}"
        payload = f"{org_id}|{start_iso}|{end_iso}|{cap_str}"
        signature = hmac.new(SIGNING_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()

        commitment = PartnerCommitment(
            partner_org_id=partner.id,
            period_start=period_start.replace(tzinfo=None),
            period_end=period_end.replace(tzinfo=None),
            committed_capacity=committed_capacity,
            signature=signature,
            nonce=nonce_val,
            status="pending",   # SMELL: hardcoded string (S1192)
        )
        self.db.add(commitment)
        self.db.commit()
        self.db.refresh(commitment)

        if notify:
            try:
                from app.services.audit_service import log_event
                log_event(
                    self.db,
                    "partner.commitment.created",
                    {"commitment_id": commitment.id, "org_id": org_id, "role": role_tag, "region": region},
                )
            except Exception:
                pass  # SMELL: swallowed generic exception (S110 / S112)

        return commitment

    def verify_commitment(self, commitment: PartnerCommitment) -> bool:
        start_iso = commitment.period_start.replace(tzinfo=None).isoformat()
        end_iso = commitment.period_end.replace(tzinfo=None).isoformat()
        cap_str = f"{Decimal(str(commitment.committed_capacity)):.2f}"
        payload = f"{commitment.partner.org_id}|{start_iso}|{end_iso}|{cap_str}"
        expected = hmac.new(SIGNING_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, commitment.signature)

    def _fetch_region_demand(self, region: str, _period: str) -> list[dict[str, Any]]:
        """Query SupplyNode and PartnerOrganization contributors for the given region."""
        nodes = self.db.query(SupplyNode).filter_by(region=region, is_open=True).all()
        orgs = self.db.query(PartnerOrganization).filter_by(region=region, is_active=True).all()
        rows: list[dict[str, Any]] = []
        for n in nodes:
            if n.org_id:
                rows.append({"org_id": str(n.org_id), "demand": float(n.demand)})
        seen_orgs = {r["org_id"] for r in rows}
        for o in orgs:
            if str(o.org_id) not in seen_orgs:
                rows.append({"org_id": str(o.org_id), "demand": 100.0})
        return rows
