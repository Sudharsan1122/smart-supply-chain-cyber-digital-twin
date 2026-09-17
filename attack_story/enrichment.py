"""Phase 16 - Threat intel enrichment (C8)."""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api_sources.registry import all_adapters
from database import models as m
from database.repository import Repository

logger = logging.getLogger(__name__)

VERDICT_WEIGHTS = {"malicious": 1.0, "suspicious": 0.6, "clean": 0.0, "unknown": 0.15}

PROVIDER_FOR_TYPE = {
    "ip": ["virustotal", "abuseipdb", "alienvault"],
    "domain": ["virustotal", "alienvault"],
    "url": ["virustotal", "alienvault"],
    "md5": ["virustotal", "alienvault"],
    "sha1": ["virustotal", "alienvault"],
    "sha256": ["virustotal", "alienvault"],
}


def consensus_verdict(verdicts):
    if not verdicts:
        return "unknown"
    if "malicious" in verdicts:
        return "malicious"
    if "suspicious" in verdicts:
        return "suspicious"
    if "clean" in verdicts:
        return "clean"
    return "unknown"


def verdict_weight(v):
    return VERDICT_WEIGHTS.get(v or "unknown", 0.0)


def providers_for(t):
    return list(PROVIDER_FOR_TYPE.get(t, []))


async def enrich_ioc(session: AsyncSession, ioc_row: m.IOC, ttl_seconds: int = 86400, force: bool = False):
    repo = Repository(session)
    providers = providers_for(ioc_row.ioc_type)
    if not providers:
        return {"ioc_id": ioc_row.id, "value": ioc_row.value,
                "ioc_type": ioc_row.ioc_type, "provider_results": [],
                "consensus": "unknown", "note": "no applicable providers"}
    adapters = all_adapters()
    provider_results = []
    verdicts = []
    for name in providers:
        adapter = adapters.get(name)
        if adapter is None:
            continue
        try:
            r = await adapter.query(ioc=ioc_row.value, ioc_type=ioc_row.ioc_type)
        except Exception as e:
            provider_results.append({"provider": name, "verdict": None, "error": str(e)[:200]})
            continue
        if not r.success:
            provider_results.append({"provider": name, "verdict": None, "error": r.error})
            continue
        verdict = (r.data or {}).get("verdict")
        if verdict:
            verdicts.append(verdict)
        await repo.ioc_enrichments.insert(ioc_db_id=ioc_row.id, provider=name,
                                          verdict=verdict, raw=r.data or {})
        provider_results.append({"provider": name, "verdict": verdict,
                                 "confidence": (r.data or {}).get("confidence")})
    consensus = consensus_verdict(verdicts)
    if consensus == "malicious":
        ioc_row.confidence = 0.95
    elif consensus == "suspicious":
        ioc_row.confidence = 0.7
    elif consensus == "clean":
        ioc_row.confidence = 0.1
    await session.flush()
    return {"ioc_id": ioc_row.id, "value": ioc_row.value, "ioc_type": ioc_row.ioc_type,
            "provider_results": provider_results, "consensus": consensus}


async def enrich_pending(session: AsyncSession, limit: int = 20, ttl_seconds: int = 86400):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
    recent = select(m.IOCEnrichment.ioc_id).where(m.IOCEnrichment.enriched_at >= cutoff).distinct()
    stmt = (select(m.IOC).where(m.IOC.id.not_in(recent))
            .order_by(m.IOC.last_seen.desc()).limit(limit))
    candidates = list((await session.execute(stmt)).scalars().all())
    summaries = []
    for ioc in candidates:
        try:
            summaries.append(await enrich_ioc(session, ioc, ttl_seconds))
        except Exception as e:
            logger.exception("Enrich failed: %s", e)
    if candidates:
        await session.commit()
    return summaries
