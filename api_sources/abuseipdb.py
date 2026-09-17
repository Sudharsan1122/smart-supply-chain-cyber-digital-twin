"""AbuseIPDB adapter."""
from api_sources.base import BaseAdapter
from config.settings import settings


class AbuseIPDBAdapter(BaseAdapter):
    name = "abuseipdb"
    base_url = "https://api.abuseipdb.com/api/v2"

    @property
    def api_key(self): return settings.abuseipdb_api_key

    def _headers(self):
        return {"Key": self.api_key, "Accept": "application/json"}

    async def _fetch(self, ioc, ioc_type, **_):
        if ioc_type != "ip":
            raise ValueError("AbuseIPDB only supports IPs")
        async with await self._client() as client:
            r = await client.get("/check", params={"ipAddress": ioc, "maxAgeInDays": 90})
            r.raise_for_status()
            d = r.json().get("data", {})
        score = d.get("abuseConfidenceScore", 0)
        verdict = "malicious" if score >= 75 else ("suspicious" if score >= 25 else "clean")
        return {"ioc": ioc, "ioc_type": "ip", "verdict": verdict,
                "abuse_score": score, "country": d.get("countryCode"),
                "confidence": round(score / 100, 3)}
