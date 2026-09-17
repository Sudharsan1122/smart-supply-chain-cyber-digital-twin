"""Phase 17 - Blast radius."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models as m
from database.repository import Repository
from digital_twin.graph import twin_graph
from digital_twin.metrics import betweenness_centrality

SEVERITY_IMPACT = {"info": 0.05, "low": 0.20, "medium": 0.45, "high": 0.75, "critical": 1.00}
DEFAULT_DECAY = 0.7
MAX_DEPTH = 5


@dataclass
class BlastRadiusResult:
    source_asset_id: str
    source_severity: str
    max_depth: int
    impacted: list[dict] = field(default_factory=list)
    by_depth: dict = field(default_factory=dict)
    total_impact: float = 0.0
    critical_assets: list[str] = field(default_factory=list)


def compute_blast_radius(source_asset_id, severity="high", max_depth=MAX_DEPTH, decay=DEFAULT_DECAY):
    if not twin_graph.has_node(source_asset_id):
        raise ValueError(f"Unknown asset: {source_asset_id}")
    base = SEVERITY_IMPACT.get(severity, 0.5)
    bc = betweenness_centrality()
    max_bc = max(bc.values()) if bc else 1.0
    centrality = {k: (v / max_bc) for k, v in bc.items()}

    result = BlastRadiusResult(source_asset_id, severity, max_depth)
    q = deque([(source_asset_id, 0, [source_asset_id])])
    visited = {source_asset_id: 0}
    by_depth = {0: 1}

    while q:
        node, depth, path = q.popleft()
        if depth >= max_depth:
            continue
        for child in twin_graph.direct_children(node):
            nd = depth + 1
            if child in visited and visited[child] <= nd:
                continue
            visited[child] = nd
            np = path + [child]
            by_depth[nd] = by_depth.get(nd, 0) + 1
            c = centrality.get(child, 0.0)
            score = base * (decay ** (nd - 1)) * (0.7 + 0.3 * c)
            score_pct = round(min(100.0, max(0.0, score * 100)), 2)
            result.impacted.append({"asset_id": child, "depth": nd,
                                    "impact_score": score_pct, "path": np})
            if score_pct >= 50:
                result.critical_assets.append(child)
            q.append((child, nd, np))

    result.by_depth = by_depth
    result.total_impact = round(sum(a["impact_score"] for a in result.impacted), 2)
    result.impacted.sort(key=lambda a: a["impact_score"], reverse=True)
    return result


async def persist_blast_radius(session: AsyncSession, result: BlastRadiusResult,
                                attack_story_db_id=None):
    repo = Repository(session)
    source_db_id = twin_graph.db_id_for(result.source_asset_id)
    if attack_story_db_id is not None:
        await repo.blast_radius.clear_for_story(attack_story_db_id)
    count = 0
    for imp in result.impacted:
        imp_db_id = twin_graph.db_id_for(imp["asset_id"])
        if imp_db_id is None:
            continue
        await repo.blast_radius.insert(
            source_asset_db_id=source_db_id, impacted_asset_db_id=imp_db_id,
            attack_story_db_id=attack_story_db_id, depth=imp["depth"],
            impact_score=imp["impact_score"], path=imp["path"],
        )
        count += 1
    await session.flush()
    return {"rows_persisted": count, "impacted_count": len(result.impacted),
            "total_impact": result.total_impact}
