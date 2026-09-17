"""AlienVault OTX adapter."""
from api_sources.base import BaseAdapter
from config.settings import settings


class AlienVaultOTXAdapter(BaseAdapter):
    name = "alienvault"
    base_url = "https://otx.alienvault.com/api/v1"

    @property
    def api_key(self): return settings.alienvault_otx_key

    def _headers(self):
        h = {"Accept": "application/json"}
        if self.api_key:
            h["X-OTX-API-KEY"] = self.api_key
        return h

    async def _fetch(self, ioc, ioc_type, **_):
        section = {"ip": "IPv4", "domain": "domain", "hash": "file", "url": "url"}.get(ioc_type)
        if not section:
            raise ValueError(f"Unsupported: {ioc_type}")
        async with await self._client() as client:
            r = await client.get(f"/indicators/{section}/{ioc}/general")
            r.raise_for_status()
            payload = r.json()
        pulse_count = payload.get("pulse_info", {}).get("count", 0)
        verdict = "malicious" if pulse_count >= 5 else ("suspicious" if pulse_count >= 1 else "clean")
        return {"ioc": ioc, "ioc_type": ioc_type, "verdict": verdict,
                "pulse_count": pulse_count,
                "confidence": round(min(1.0, pulse_count / 10), 3)}
