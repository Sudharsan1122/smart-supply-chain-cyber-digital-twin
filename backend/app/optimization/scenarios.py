"""Scenario parameter modifiers for MILP optimization runs."""
from __future__ import annotations

from app.optimization.storage_interface import NodeData


def apply_demand_multiplier(nodes: list[NodeData], multiplier: float) -> list[NodeData]:
    """Scale node demand values by the specified multiplier for stress-test optimization.

    Args:
        nodes: Original list of NodeData objects.
        multiplier: Positive demand scaling factor.

    Returns:
        New list of NodeData with scaled demand values.
    """
    return [
        NodeData(
            node_code=n.node_code,
            node_type=n.node_type,
            capacity=n.capacity,
            fixed_cost=n.fixed_cost,
            inventory=n.inventory,
            demand=round(n.demand * multiplier, 2),
        )
        for n in nodes
    ]
