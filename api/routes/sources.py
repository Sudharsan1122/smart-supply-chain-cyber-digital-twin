"""External source adapters."""
from fastapi import APIRouter, HTTPException
from api_sources.registry import all_adapters

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("")
async def list_adapters():
    out = []
    for name, a in all_adapters().items():
        out.append({"name": name, "base_url": a.base_url,
                    "requires_api_key": a.requires_api_key,
                    "configured": bool(a.api_key) if a.requires_api_key else True,
                    "cache_entries": a.cache_stats()["entries"]})
    return out


@router.post("/ioc-lookup")
async def ioc_lookup(payload: dict):
    ioc = payload.get("ioc")
    ioc_type = payload.get("ioc_type")
    if not ioc or not ioc_type:
        raise HTTPException(400, "ioc and ioc_type required")
    results = []
    for name in ("virustotal", "abuseipdb", "alienvault"):
        adapter = all_adapters().get(name)
        if adapter is None:
            continue
        try:
            r = await adapter.query(ioc=ioc, ioc_type=ioc_type)
            results.append(r.to_dict())
        except Exception as e:
            results.append({"source": name, "success": False, "error": str(e)[:200]})
    return {"ioc": ioc, "ioc_type": ioc_type, "results": results}
