"""MILP optimization, storage abstraction, and cryptographic audit chain verification tests."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_milp_optimization_and_audit_verification(
    client: TestClient,
    planner_headers: dict[str, str],
) -> None:
    """Verify PuLP MILP solver returns optimal facility opening, flow allocations, and valid audit chain."""
    opt_res = client.post(
        "/optimize",
        json={"trigger_reason": "STRESS_TEST_120PCT", "demand_multiplier": 1.2},
        headers=planner_headers,
    )
    assert opt_res.status_code == 200
    data = opt_res.json()
    assert data["status"] == "OPTIMAL"
    assert data["objective_cost"] > 0.0
    assert len(data["open_facilities"]) >= 1
    assert isinstance(data["flow_allocations"], dict)

    logs_res = client.get("/audit/logs", headers=planner_headers)
    assert logs_res.status_code == 200
    assert len(logs_res.json()) >= 1

    verify_res = client.get("/audit/verify", headers=planner_headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["chain_valid"] is True
