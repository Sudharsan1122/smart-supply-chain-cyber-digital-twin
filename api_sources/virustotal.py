"""VirusTotal adapter."""
from typing import Any
from api_sources.base import BaseAdapter
from config.settings import settings


class VirusTotalAdapter(BaseAdapter):
    name = "virustotal"
    base_url = "https://www.virustotal.com/api/v3"

    @property
    def api_key(self): return settings.virustotal_api_key

    def _headers(self):
        return {"x-apikey": self.api_key, "Accept": "application/json"}

    async def _fetch(self, ioc, ioc_type, **_):
        endpoint = {"ip": f"/ip_addresses/{ioc}", "domain": f"/domains/{ioc}",
                    "hash": f"/files/{ioc}", "url": f"/urls/{ioc}"}.get(ioc_type)
        if not endpoint:
            raise ValueError(f"Unsupported: {ioc_type}")
        async with await self._client() as client:
            r = await client.get(endpoint)
            r.raise_for_status()
            payload = r.json()
        attrs = payload.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total = sum(stats.values()) or 1
        verdict = "malicious" if malicious >= 3 else ("suspicious" if malicious + suspicious > 0 else "clean")
        return {"ioc": ioc, "ioc_type": ioc_type, "verdict": verdict,
                "malicious": malicious, "suspicious": suspicious,
                "confidence": round(min(1.0, (malicious + suspicious) / total), 3)}
