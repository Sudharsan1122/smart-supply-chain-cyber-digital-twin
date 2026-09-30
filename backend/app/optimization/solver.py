"""Mixed-Integer Linear Programming (MILP) facility location and flow allocation solver using PuLP."""
from __future__ import annotations

import pulp

from app.optimization.scenarios import apply_demand_multiplier
from app.optimization.storage_interface import (
    EdgeData,
    NodeData,
    OptimizationResultData,
    OptimizationStorageInterface,
)

UNMET_DEMAND_PENALTY = 500.0


def _build_milp_problem(
    nodes: list[NodeData],
    edges: list[EdgeData],
) -> tuple[pulp.LpProblem, dict[str, pulp.LpVariable], dict[str, pulp.LpVariable]]:
    """Construct the PuLP MILP facility opening and network flow optimization model."""
    prob = pulp.LpProblem("SupplyChain_Facility_Flow_MILP", pulp.LpMinimize)
    open_vars = {n.node_code: pulp.LpVariable(f"open_{n.node_code}", cat=pulp.LpBinary) for n in nodes}
    flow_vars = {
        e.edge_code: pulp.LpVariable(f"flow_{e.edge_code}", lowBound=0.0, upBound=e.max_flow)
        for e in edges
    }
    slack_vars = {
        n.node_code: pulp.LpVariable(f"unmet_{n.node_code}", lowBound=0.0)
        for n in nodes
        if n.demand > 0
    }

    fixed_cost_expr = pulp.lpSum(n.fixed_cost * open_vars[n.node_code] for n in nodes)
    flow_cost_expr = pulp.lpSum(e.unit_cost * flow_vars[e.edge_code] for e in edges)
    penalty_expr = pulp.lpSum(UNMET_DEMAND_PENALTY * slack_vars[c] for c in slack_vars)
    prob += fixed_cost_expr + flow_cost_expr + penalty_expr

    for n in nodes:
        code = n.node_code
        inflow = pulp.lpSum(flow_vars[e.edge_code] for e in edges if e.target_node_code == code)
        outflow = pulp.lpSum(flow_vars[e.edge_code] for e in edges if e.source_node_code == code)
        prob += outflow <= n.capacity * open_vars[code], f"Cap_{code}"
        if n.demand > 0:
            prob += inflow + n.inventory * open_vars[code] + slack_vars[code] >= n.demand, f"Demand_{code}"
    return prob, open_vars, flow_vars


def run_network_optimization(
    storage: OptimizationStorageInterface,
    trigger_reason: str = "MANUAL",
    actor: str = "PLANNER",
    demand_multiplier: float = 1.0,
) -> OptimizationResultData:
    """Solve the MILP facility opening and flow allocation problem and persist via storage interface.

    Args:
        storage: Abstract storage adapter implementing OptimizationStorageInterface.
        trigger_reason: Reason string for audit trail.
        actor: Username or system trigger initiating the optimization.
        demand_multiplier: Optional scaling factor for node demand.

    Returns:
        OptimizationResultData with optimal cost, open facilities, and lane flows.
    """
    raw_nodes, edges = storage.load_network()
    nodes = apply_demand_multiplier(raw_nodes, demand_multiplier)
    prob, open_vars, flow_vars = _build_milp_problem(nodes, edges)
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    status_str = pulp.LpStatus.get(prob.status, "Optimal")
    objective_val = round(float(pulp.value(prob.objective) or 0.0), 2)
    opened = [code for code, var in open_vars.items() if (var.varValue or 0.0) >= 0.5]
    flows = {code: round(float(var.varValue or 0.0), 2) for code, var in flow_vars.items()}
    return storage.save_result(
        trigger_reason=trigger_reason,
        status=status_str.upper(),
        objective_cost=objective_val,
        open_facilities=opened,
        flow_allocations=flows,
        actor=actor,
    )
