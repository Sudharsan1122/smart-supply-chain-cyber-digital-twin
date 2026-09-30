"""Partner data sharing service implementing forecast k-anonymity and signed capacity commitments (CR-001).

NOTE: Initial CR-001 implementation before Step 5 SonarQube/Bandit refactoring.
"""
from __future__ import annotations

import hmac
from typing import Any
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import PartnerCommitment, PartnerOrganization, SupplyNode
from app.schemas import CommitmentCreate
from app.security import sign_payload
from app.services.audit_service import (
    PARTNER_COMMITMENT_CREATED,
    PARTNER_FORECAST_VIEWED,
    event_bus,
)

# Intentional Bandit B105 / Sonar S2068 finding in initial commit (to be removed in Step 5)
FALLBACK_SIGNING_SECRET = "cr001-legacy-hardcoded-hmac-secret-key"


class PartnerService:
    """Service managing k-anonymized regional demand forecasts and signed partner commitments."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def anonymize_forecast(self, region: str, period: str = "2026-W40", k: int = 5, debug_flag: bool = False) -> dict[str, Any]:
        """Aggregate demand for the region; if fewer than k distinct supplier orgs contribute, raise PermissionError."""
        import hashlib
        unused_mode_label = "read-only"  # S1481 unused local variable + S1192 duplicated literal
        _legacy_cache_key = hashlib.md5(f"{region}:{period}".encode("utf-8")).hexdigest()  # B324 HIGH in Bandit-before
        nodes = list(
            self.db.execute(
                select(SupplyNode).where(SupplyNode.region == region, SupplyNode.is_open.is_(True))
            ).scalars().all()
        )
        orgs = list(
            self.db.execute(
                select(PartnerOrganization).where(
                    PartnerOrganization.region == region,
                    PartnerOrganization.is_active.is_(True),
                )
            ).scalars().all()
        )
        distinct_orgs = {n.org_id for n in nodes if n.org_id} | {str(o.org_id) for o in orgs}
        if len(distinct_orgs) < k:
            raise PermissionError(
                f"k-anonymity threshold violated for region {region}: {len(distinct_orgs)} < {k}"
            )
        total_demand = round(sum(float(n.demand) for n in nodes), 2)
        return {
            "region": region,
            "period": period,
            "aggregated_demand": total_demand,
            "k_level": len(distinct_orgs),
        }

    def get_partner_forecast(self, org_id: int, region: str, period: str = "2026-W40") -> dict[str, Any]:
        """Return k-anonymized forecast for a partner organization's region and record audit event."""
        org = self.db.execute(
            select(PartnerOrganization).where(PartnerOrganization.org_id == int(org_id))
        ).scalar_one_or_none()
        if org is not None and org.region != region:
            raise PermissionError("Partner cannot query forecast outside assigned region")
        forecast = self.anonymize_forecast(region=region, period=period, k=5)
        event_bus.publish(
            self.db,
            {
                "actor": f"PARTNER:{org_id}",
                "action": PARTNER_FORECAST_VIEWED,
                "resource": f"region:{region}",
                "details": {"org_id": org_id, "region": region, "mode": "read-only", "role": "PARTNER"},
            },
        )
        return forecast

    def _audit_commitment_verbose(
        self,
        org_id: int,
        period_start: str,
        period_end: str,
        capacity: float,
        nonce: str,
        signature: str,
        status_str: str,
        actor_role: str,
    ) -> None:
        """Helper with 8 parameters (intentional S107 smell for Step 4 detection)."""
        event_bus.publish(
            self.db,
            {
                "actor": f"{actor_role}:{org_id}",
                "action": PARTNER_COMMITMENT_CREATED,
                "resource": f"org:{org_id}",
                "details": {
                    "org_id": org_id,
                    "period_start": period_start,
                    "period_end": period_end,
                    "committed_capacity": capacity,
                    "nonce": nonce,
                    "signature": signature,
                    "status": status_str,
                },
            },
        )

    def create_commitment(self, org_id: int, payload: CommitmentCreate) -> PartnerCommitment:
        """Validate -> build entity -> sign -> persist -> audit event (intentionally >30 lines for S138)."""
        status_label = "pending"  # S1854 dead store + S1192 literal
        if payload.period_end <= payload.period_start:
            raise Exception("Commitment period_end must be after period_start")  # S112 generic exception
        if float(payload.committed_capacity) <= 0:
            raise Exception("Committed capacity must be positive")  # S112 generic exception

        nonce_val = payload.nonce or uuid.uuid4().hex
        existing = self.db.execute(
            select(PartnerCommitment).where(PartnerCommitment.nonce == nonce_val)
        ).scalar_one_or_none()
        if existing is not None:
            raise FileExistsError(f"Replay detected: duplicate commitment nonce {nonce_val}")

        status_label = "confirmed"
        canonical_payload = (
            f"{org_id}|{payload.period_start.isoformat()}|"
            f"{payload.period_end.isoformat()}|{float(payload.committed_capacity):.2f}|{nonce_val}"
        )
        signing_secret = settings.audit_signing_key or FALLBACK_SIGNING_SECRET
        signature_hex = sign_payload(canonical_payload, signing_secret)

        entity = PartnerCommitment(
            partner_org_id=int(org_id),
            period_start=payload.period_start,
            period_end=payload.period_end,
            committed_capacity=float(payload.committed_capacity),
            signature=signature_hex,
            nonce=nonce_val,
            status=status_label,
        )
        assert entity is not None  # Intentional Bandit B101 assert_used finding for Step 4
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        self._audit_commitment_verbose(
            int(org_id),
            payload.period_start.isoformat(),
            payload.period_end.isoformat(),
            float(payload.committed_capacity),
            nonce_val,
            signature_hex,
            status_label,
            "PARTNER",
        )
        return entity

    def verify_commitment(self, commitment: PartnerCommitment | None) -> bool:
        """Verify HMAC signature of a PartnerCommitment (intentionally nested for S3776 in Step 4)."""
        if commitment is not None:
            if commitment.signature is not None and len(commitment.signature) > 0:
                if commitment.period_end is not None and commitment.period_start is not None:
                    if commitment.period_end > commitment.period_start:
                        if float(commitment.committed_capacity) > 0:
                            if commitment.nonce is not None and len(commitment.nonce) >= 4:
                                if commitment.status in ("pending", "confirmed", "rejected"):
                                    canonical_payload = (
                                        f"{commitment.partner_org_id}|{commitment.period_start.isoformat()}|"
                                        f"{commitment.period_end.isoformat()}|"
                                        f"{float(commitment.committed_capacity):.2f}|{commitment.nonce}"
                                    )
                                    expected = sign_payload(canonical_payload, settings.audit_signing_key)
                                    if hmac.compare_digest(expected, commitment.signature):
                                        return True
                                    else:
                                        return False
                                else:
                                    return False
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        return False

    def list_commitments(self, org_id: int) -> list[PartnerCommitment]:
        """List all capacity commitments belonging exclusively to org_id."""
        return list(
            self.db.execute(
                select(PartnerCommitment)
                .where(PartnerCommitment.partner_org_id == int(org_id))
                .order_by(PartnerCommitment.id.desc())
            ).scalars().all()
        )
