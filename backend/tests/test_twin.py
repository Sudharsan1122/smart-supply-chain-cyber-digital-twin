"""Digital Twin topology, bidirectional sync, >5% drift auto-trigger, and simulation tests."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_twin_state_and_ingest_topology(
    client: TestClient,
    planner_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    """Verify 10-node seeded network snapshot, node/edge upsert, and VIEWER RBAC restriction."""
    state_res = client.get("/twin/state", headers=viewer_headers)
    assert state_res.status_code == 200
    snapshot = state_res.json()
    assert snapshot["node_count"] == 10
    assert snapshot["edge_count"] == 10

    node_payload = {
        "node_code": "WH-004",
        "name": "Chennai Cold Storage",
        "node_type": "WAREHOUSE",
        "capacity": 950.0,
        "fixed_cost": 2800.0,
        "inventory": 400.0,
        "demand": 150.0,
        "is_open": True,
        "org_id": None,
    }
    forbidden_res = client.post("/twin/nodes", json=node_payload, headers=viewer_headers)
    assert forbidden_res.status_code == 403

    created_node = client.post("/twin/nodes", json=node_payload, headers=planner_headers)
    assert created_node.status_code == 200
    assert created_node.json()["node_code"] == "WH-004"

    # Update existing node
    node_payload["capacity"] = 1050.0
    updated_node = client.post("/twin/nodes", json=node_payload, headers=planner_headers)
    assert updated_node.status_code == 200
    assert updated_node.json()["capacity"] == 1050.0

    edge_payload = {
        "edge_code": "LANE-11",
        "source_node_code": "FAC-001",
        "target_node_code": "WH-004",
        "lead_time_days": 1.5,
        "unit_cost": 2.7,
        "max_flow": 500.0,
        "is_active": True,
    }
    created_edge = client.post("/twin/edges", json=edge_payload, headers=planner_headers)
    assert created_edge.status_code == 200
    assert created_edge.json()["edge_code"] == "LANE-11"


def test_bidirectional_sync_and_auto_reoptimization_trigger(
    client: TestClient,
    planner_headers: dict[str, str],
) -> None:
    """Verify <=5% drift does not re-optimize while >5% drift automatically triggers MILP."""
    # RET-001 initial demand is 420.0 -> 428.0 is +1.9% (<= 5%)
    small_drift = client.post(
        "/twin/sync",
        json={"node_code": "RET-001", "demand": 428.0},
        headers=planner_headers,
    )
    assert small_drift.status_code == 200
    assert small_drift.json()["reoptimization"]["triggered"] is False

    # RET-001 demand jump from 428.0 to 520.0 is +21.5% (> 5%) -> triggers MILP
    large_drift = client.post(
        "/twin/sync",
        json={"node_code": "RET-001", "demand": 520.0, "inventory": 280.0, "capacity": 920.0},
        headers=planner_headers,
    )
    assert large_drift.status_code == 200
    reopt = large_drift.json()["reoptimization"]
    assert reopt["triggered"] is True
    assert reopt["optimization_id"] is not None

    missing_sync = client.post(
        "/twin/sync",
        json={"node_code": "NON-EXISTENT", "demand": 100.0},
        headers=planner_headers,
    )
    assert missing_sync.status_code == 404


def test_isolated_disruption_simulations(
    client: TestClient,
    planner_headers: dict[str, str],
) -> None:
    """Test SUPPLIER_FAILURE, DEMAND_SPIKE, and PORT_CLOSURE isolated simulations."""
    for scenario, target in [
        ("SUPPLIER_FAILURE", "SUP-001"),
        ("DEMAND_SPIKE", "RET-001"),
        ("PORT_CLOSURE", "PRT-001"),
    ]:
        sim_res = client.post(
            "/simulate",
            json={
                "scenario_type": scenario,
                "target_node_code": target,
                "severity_pct": 60.0,
                "duration_days": 14,
            },
            headers=planner_headers,
        )
        assert sim_res.status_code == 200
        body = sim_res.json()
        assert body["status"] == "COMPLETED"
        assert 0.0 <= body["service_level_pct"] <= 100.0
        assert len(body["recommendations"]) >= 2
