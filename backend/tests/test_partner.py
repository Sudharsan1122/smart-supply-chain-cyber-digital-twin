from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.exceptions import PartnerKAnonymityError
from app.models import PartnerCommitment
from app.services.partner_service import PartnerService


def test_partner_can_view_own_forecast(client: TestClient, partner_token: str) -> None:
    r = client.get("/api/partner/forecast", headers={"Authorization": f"Bearer {partner_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["region"] == "SOUTH"
    assert body["k_level"] >= 5


def test_partner_cannot_view_other_org_forecast(
    client: TestClient,
    partner_token: str,
    viewer_token: str,
) -> None:
    r_cross = client.get(
        "/api/partner/forecast?org_id=102",
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert r_cross.status_code == 403

    r_viewer = client.get("/api/partner/forecast", headers={"Authorization": f"Bearer {viewer_token}"})
    assert r_viewer.status_code == 403


def test_k_anonymity_enforced(
    client: TestClient,
    partner_token: str,
    db_session: Session,
) -> None:
    r = client.get("/api/partner/forecast", headers={"Authorization": f"Bearer {partner_token}"})
    assert r.status_code == 200
    assert r.json()["k_level"] >= 5

    svc = PartnerService(db_session)
    with pytest.raises(PartnerKAnonymityError):
        svc.anonymize_forecast("NORTH", "2026-W40", k=5)


def test_commitment_signature_is_valid(
    client: TestClient,
    partner_token: str,
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "period_start": now.isoformat(),
        "period_end": (now + timedelta(days=7)).isoformat(),
        "committed_capacity": "100.00",
    }
    r = client.post(
        "/api/partner/commit",
        json=payload,
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert r.status_code in (200, 201)
    data = r.json()
    assert "signature" in data

    record = db_session.get(PartnerCommitment, data["id"])
    assert record is not None
    svc = PartnerService(db_session)
    assert svc.verify_commitment(record) is True

    r_list = client.get("/api/partner/commitments", headers={"Authorization": f"Bearer {partner_token}"})
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1


def test_commitment_replay_rejected(client: TestClient, partner_token: str) -> None:
    now = datetime.now(timezone.utc)
    payload = {
        "period_start": now.isoformat(),
        "period_end": (now + timedelta(days=7)).isoformat(),
        "committed_capacity": "50.00",
        "nonce": "nonce-fixed-replay-check-001",
    }
    r1 = client.post(
        "/api/partner/commit",
        json=payload,
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    r2 = client.post(
        "/api/partner/commit",
        json=payload,
        headers={"Authorization": f"Bearer {partner_token}"},
    )
    assert r1.status_code in (200, 201)
    assert r2.status_code == 409


def test_viewer_cannot_access_partner_endpoint(client: TestClient, viewer_token: str) -> None:
    r = client.get("/api/partner/forecast", headers={"Authorization": f"Bearer {viewer_token}"})
    assert r.status_code == 403


def test_planner_cannot_access_partner_endpoint(client: TestClient, planner_token: str) -> None:
    r = client.get("/api/partner/forecast", headers={"Authorization": f"Bearer {planner_token}"})
    assert r.status_code == 403
