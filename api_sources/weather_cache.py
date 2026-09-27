"""15-minute TTL cache for OpenWeather responses."""
from __future__ import annotations

import asyncio
import time
from typing import Any

from api_sources.openweather import OpenWeatherAdapter
from config.settings import settings

_cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
_ttl = 900  # 15 minutes


async def get_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """Return cached or freshly fetched weather for (lat, lon)."""
    # Round to 2 decimals so nearby assets share cache
    key = (round(float(lat), 2), round(float(lon), 2))
    now = time.time()
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < _ttl:
            return data
    if not settings.openweather_api_key:
        return None
    adapter = OpenWeatherAdapter()
    result = await adapter.query(lat=key[0], lon=key[1])
    if result.success and result.data:
        _cache[key] = (now, result.data)
        return result.data
    return None


async def get_weather_batch(coords: dict[str, tuple[float, float]]) -> dict[str, dict[str, Any]]:
    """Fetch weather for multiple assets concurrently, deduplicating by rounded coordinates."""
    if not settings.openweather_api_key or not coords:
        return {}

    unique_keys: set[tuple[float, float]] = {
        (round(float(lat), 2), round(float(lon), 2))
        for lat, lon in coords.values()
    }

    async def _fetch_key(k: tuple[float, float]) -> tuple[tuple[float, float], dict[str, Any] | None]:
        return k, await get_weather(k[0], k[1])

    results = await asyncio.gather(*(_fetch_key(k) for k in unique_keys), return_exceptions=True)
    by_key: dict[tuple[float, float], dict[str, Any]] = {}
    for item in results:
        if isinstance(item, tuple) and item[1]:
            by_key[item[0]] = item[1]

    out: dict[str, dict[str, Any]] = {}
    for aid, (lat, lon) in coords.items():
        k = (round(float(lat), 2), round(float(lon), 2))
        if k in by_key:
            out[aid] = by_key[k]
    return out


def clear() -> None:
    """Clear the weather cache."""
    _cache.clear()
