"""Phase 15 - IOC extraction."""
from __future__ import annotations
import ipaddress, logging, re
from dataclasses import dataclass, field
from typing import Any, Iterable

logger = logging.getLogger(__name__)

_RESERVED = {"example.com", "example.org", "example.net", "localhost", "test", "invalid", "local"}

def _is_private(ip):
    try:
        o = ipaddress.ip_address(ip)
        return o.is_private or o.is_loopback or o.is_link_local or o.is_multicast or o.is_reserved or o.is_unspecified
    except ValueError:
        return True

def _is_reserved_domain(d):
    d = d.lower().rstrip(".")
    return any(d == r or d.endswith("." + r) for r in _RESERVED)

RE_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")
RE_DOMAIN = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,24})\b", re.IGNORECASE)
RE_URL = re.compile(r"\bhttps?://[^\s\"'<>]+", re.IGNORECASE)
RE_SHA256 = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
RE_SHA1 = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
RE_MD5 = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_MQTT = re.compile(r"\bsupply_chain/[A-Za-z0-9_\-/]+", re.IGNORECASE)


@dataclass
class ExtractedIOC:
    value: str
    ioc_type: str
    source: str
    context: dict[str, Any] = field(default_factory=dict)


def _extract_from_string(text, source, base_context=None):
    if not text:
        return []
    ctx = dict(base_context or {})
    out = []
    for url in RE_URL.findall(text):
        out.append(ExtractedIOC(value=url, ioc_type="url", source=source, context=ctx))
    for ip in RE_IPV4.findall(text):
        if not _is_private(ip):
            out.append(ExtractedIOC(value=ip, ioc_type="ip", source=source, context=ctx))
    for d in RE_DOMAIN.findall(text):
        if not _is_reserved_domain(d):
            out.append(ExtractedIOC(value=d.lower(), ioc_type="domain", source=source, context=ctx))
    for e in RE_EMAIL.findall(text):
        out.append(ExtractedIOC(value=e.lower(), ioc_type="email", source=source, context=ctx))
    for h in RE_SHA256.findall(text):
        out.append(ExtractedIOC(value=h.lower(), ioc_type="sha256", source=source, context=ctx))
    for h in RE_SHA1.findall(text):
        if len(h) == 40:
            out.append(ExtractedIOC(value=h.lower(), ioc_type="sha1", source=source, context=ctx))
    for h in RE_MD5.findall(text):
        if len(h) == 32:
            out.append(ExtractedIOC(value=h.lower(), ioc_type="md5", source=source, context=ctx))
    for t in RE_MQTT.findall(text):
        out.append(ExtractedIOC(value=t, ioc_type="mqtt_topic", source=source, context=ctx))
    return out


def _walk(v: Any) -> Iterable[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _walk(x)
    elif isinstance(v, (list, tuple, set)):
        for x in v:
            yield from _walk(x)


def extract_from_dict(data, source, context=None):
    found = []
    for s in _walk(data):
        found += _extract_from_string(s, source, base_context=context)
    seen = {}
    for i in found:
        key = (i.ioc_type, i.value.lower() if i.ioc_type == "domain" else i.value)
        if key not in seen:
            seen[key] = i
    return list(seen.values())


def extract_from_telemetry(payload):
    data = payload.model_dump(mode="json")
    ctx = {"asset_id": data.get("asset_id"), "asset_type": data.get("asset_type")}
    return extract_from_dict(data, "telemetry", context=ctx)


def extract_from_event(payload):
    data = payload.model_dump(mode="json")
    ctx = {"asset_id": data.get("asset_id"), "event_type": data.get("event_type")}
    return extract_from_dict(data, "event", context=ctx)


async def persist_iocs(session, iocs, asset_db_id=None, attack_story_db_id=None):
    if not iocs:
        return []
    from database.repository import Repository
    repo = Repository(session)
    out = []
    for it in iocs:
        row = await repo.iocs.upsert(value=it.value, ioc_type=it.ioc_type, source=it.source)
        out.append({"ioc_id": row.id, "value": row.value, "ioc_type": row.ioc_type})
    return out
