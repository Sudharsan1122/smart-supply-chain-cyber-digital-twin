"""Unit and integration tests for CR-001 Partner Data Sharing (forecast k-anonymity, RLS, HMAC, replay defense)."""
from __future__ import annotations

from datetime import date
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.models import PartnerCommitment
from app.services.partner_service import PartnerService


def test_partner_can_view_own_forecast(
    client: TestClient,
    partner_headers: dict[str, str],
) -> None:
    """Verify an authenticated PARTNER can view the k-anonymized demand forecast for their own org and region."""
    resp = client.get("/api/partner/forecast?org_id=101&region=SOUTH&period=2026-W40", headers=partner_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["region"] == "SOUTH"
    assert body["period"] == "2026-W40"
    assert body["k_level"] >= 5
    assert body["aggregated_demand"] > 0


def test_partner_cannot_view_other_org_forecast(
    client: TestClient,
    partner_headers: dict[str, str],
) -> None:
    """Verify Partner A (org_id=101) receives 403 Forbidden when requesting Partner B's (org_id=102) forecast."""
    resp = client.get("/api/partner/forecast?org_id=102&region=SOUTH", headers=partner_headers)
    assert resp.status_code == 403
    assert "org_id mismatch" in resp.json()["detail"]


def test_k_anonymity_enforced(db_session: Session) -> None:
    """Verify PartnerService.anonymize_forecast raises PermissionError when fewer than k=5 orgs contribute."""
    svc = PartnerService(db_session)
    with pytest.raises(PermissionError, match="k-anonymity threshold violated"):
        svc.anonymize_forecast(region="NORTH", period="2026-W40", k=5)


def test_commitment_signature_is_valid(
    client: TestClient,
    partner_headers: dict[str, str],
    db_session: Session,
) -> None:
    """Verify submitted commitments are HMAC-SHA256 signed and pass PartnerService.verify_commitment()."""
    payload = {
        "period_start": str(date(2026, 10, 1)),
        "period_end": str(date(2026, 10, 7)),
        "committed_capacity": 850.0,
        "nonce": "nonce-unique-cr001-001",
    }
    resp = client.post("/api/partner/commit?org_id=101", json=payload, headers=partner_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["signature"]) == 64

    record = db_session.get(PartnerCommitment, data["id"])
    assert record is not None
    svc = PartnerService(db_session)
    assert svc.verify_commitment(record) is True

    list_resp = client.get("/api/partner/commitments?org_id=101", headers=partner_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_commitment_replay_rejected(
    client: TestClient,
    partner_headers: dict[str, str],
) -> None:
    """Verify reusing a commitment nonce is rejected with HTTP 409 Conflict."""
    payload = {
        "period_start": str(date(2026, 10, 8)),
        "period_end": str(date(2026, 10, 14)),
        "committed_capacity": 920.0,
        "nonce": "nonce-replay-attack-999",
    }
    first = client.post("/api/partner/commit", json=payload, headers=partner_headers)
    assert first.status_code == 201

    replay = client.post("/api/partner/commit", json=payload, headers=partner_headers)
    assert replay.status_code == 409
    assert "Replay detected" in replay.json()["detail"]


def test_viewer_cannot_access_partner_endpoint(
    client: TestClient,
    viewer_headers: dict[str, str],
) -> None:
    """Verify VIEWER role is rejected with 403 Forbidden on /api/partner/forecast."""
    resp = client.get("/api/partner/forecast", headers=viewer_headers)
    assert resp.status_code == 403


def test_planner_cannot_access_partner_endpoint(
    client: TestClient,
    planner_headers: dict[str, str],
) -> None:
    """Verify PLANNER role is rejected with 403 Forbidden on /api/partner/commit."""
    payload = {
        "period_start": str(date(2026, 10, 1)),
        "period_end": str(date(2026, 10, 7)),
        "committed_capacity": 500.0,
        "nonce": "nonce-planner-attempt",
    }
    resp = client.post("/api/partner/commit", json=payload, headers=planner_headers)
    assert resp.status_code == 403
