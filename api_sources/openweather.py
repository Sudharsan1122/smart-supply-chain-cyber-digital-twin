"""OpenWeather adapter."""
from api_sources.base import BaseAdapter
from config.settings import settings


class OpenWeatherAdapter(BaseAdapter):
    name = "openweather"
    base_url = "https://api.openweathermap.org/data/2.5"

    @property
    def api_key(self): return settings.openweather_api_key

    async def _fetch(self, lat, lon, **_):
        async with await self._client() as client:
            r = await client.get("/weather", params={
                "lat": lat, "lon": lon, "appid": self.api_key, "units": "metric",
            })
            r.raise_for_status()
            p = r.json()
        main = p.get("main", {})
        weather0 = (p.get("weather") or [{}])[0]
        wind = p.get("wind") or {}
        return {
            "lat": lat,
            "lon": lon,
            "temperature_c": main.get("temp"),
            "humidity_pct": main.get("humidity"),
            "city": p.get("name"),
            "condition": weather0.get("main"),
            "description": weather0.get("description"),
            "wind_speed_ms": wind.get("speed"),
            "wind_deg": wind.get("deg"),
        }
