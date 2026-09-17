"""Phase 4 - Base adapter."""
from __future__ import annotations
import asyncio, hashlib, logging, time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AdapterResult:
    source: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    cached: bool = False
    fetched_at: float = field(default_factory=time.time)

    def to_dict(self):
        return {"source": self.source, "success": self.success, "cached": self.cached,
                "fetched_at": self.fetched_at, "data": self.data, "error": self.error}


class _TTLCache:
    def __init__(self, ttl):
        self.ttl = ttl
        self._s = {}
    def get(self, k):
        e = self._s.get(k)
        if e is None: return None
        ts, r = e
        if time.time() - ts > self.ttl:
            self._s.pop(k, None)
            return None
        return r
    def set(self, k, v): self._s[k] = (time.time(), v)
    def clear(self): self._s.clear()
    def stats(self): return {"entries": len(self._s)}


class _RateLimiter:
    def __init__(self, per_minute):
        self.per_minute = per_minute
        self._calls = []
    async def acquire(self):
        now = time.time()
        self._calls = [t for t in self._calls if t > now - 60]
        if len(self._calls) >= self.per_minute:
            wait = 60 - (now - self._calls[0])
            if wait > 0:
                await asyncio.sleep(wait)
        self._calls.append(time.time())


class BaseAdapter(ABC):
    name = "base"
    base_url = ""
    requires_api_key = True

    def __init__(self):
        self.timeout = settings.adapter_timeout_seconds
        self.max_retries = settings.adapter_max_retries
        self.backoff = settings.adapter_backoff_factor
        self.cache = _TTLCache(settings.adapter_cache_ttl_seconds)
        self.limiter = _RateLimiter(settings.adapter_rate_limit_per_minute)

    async def query(self, **params) -> AdapterResult:
        if not settings.external_apis_enabled:
            return AdapterResult(source=self.name, success=False, error="External APIs disabled")
        if self.requires_api_key and not self.api_key:
            return AdapterResult(source=self.name, success=False,
                                 error=f"{self.name}: API key not configured")
        key = self._cache_key(params)
        cached = self.cache.get(key)
        if cached is not None:
            cached.cached = True
            return cached
        await self.limiter.acquire()
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                data = await self._fetch(**params)
                r = AdapterResult(source=self.name, success=True, data=data)
                self.cache.set(key, r)
                return r
            except httpx.HTTPStatusError as e:
                last_err = f"HTTP {e.response.status_code}"
                if e.response.status_code < 500:
                    break
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
            if attempt < self.max_retries:
                await asyncio.sleep(self.backoff * (2 ** (attempt - 1)))
        return AdapterResult(source=self.name, success=False, error=last_err)

    @property
    def api_key(self):
        return ""

    @abstractmethod
    async def _fetch(self, **params): ...

    def _cache_key(self, params):
        raw = f"{self.name}:" + "|".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _client(self):
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout,
                                 headers=self._headers())

    def _headers(self):
        return {"Accept": "application/json"}

    def cache_stats(self): return self.cache.stats()
    def clear_cache(self): self.cache.clear()
