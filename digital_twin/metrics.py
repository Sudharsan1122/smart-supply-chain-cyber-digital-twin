"""Phase 3 - Topology metrics."""
from __future__ import annotations
from typing import Any
import networkx as nx
from digital_twin.graph import twin_graph


def graph_summary() -> dict[str, Any]:
    g = twin_graph.graph
    if g.number_of_nodes() == 0:
        return {"nodes": 0, "edges": 0, "density": 0.0, "is_dag": True,
                "roots": [], "leaves": []}
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "density": round(nx.density(g), 4),
        "is_dag": nx.is_directed_acyclic_graph(g),
        "roots": [n for n in g.nodes if g.in_degree(n) == 0],
        "leaves": [n for n in g.nodes if g.out_degree(n) == 0],
    }


def degree_centrality() -> dict[str, float]:
    g = twin_graph.graph
    if g.number_of_nodes() == 0:
        return {}
    return {k: round(v, 4) for k, v in nx.degree_centrality(g).items()}


def betweenness_centrality() -> dict[str, float]:
    g = twin_graph.graph
    if g.number_of_nodes() == 0:
        return {}
    return {k: round(v, 4) for k, v in nx.betweenness_centrality(g).items()}


def critical_nodes(top_n: int = 5) -> list[dict[str, Any]]:
    bc = betweenness_centrality()
    ranked = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"asset_id": aid, "betweenness": score, **twin_graph.graph.nodes[aid]}
            for aid, score in ranked]
