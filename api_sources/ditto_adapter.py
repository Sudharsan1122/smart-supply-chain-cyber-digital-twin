"""
Eclipse Ditto Digital Twin adapter.

Syncs our internal twin state to Eclipse Ditto's REST API.
Ditto represents each asset as a "Thing" with:
  - thingId: <namespace>:<asset_id>  e.g. "sscdt:VGW-101"
  - attributes: static metadata (asset_id, asset_type, name, parent, created_at)
  - features: dynamic state (state, risk, position, metrics)

Runs as a background loop every 5 seconds.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DITTO_URL = os.getenv("DITTO_URL", "http://localhost:8080/api/2")
DITTO_AUTH = ("ditto", "ditto")
DITTO_NAMESPACE = "sscdt"
DITTO_HEADERS = {
    "Content-Type": "application/json",
    "x-ditto-pre-authenticated": "nginx:ditto",
}


class DittoAdapter:
    """Pushes our twin state to Eclipse Ditto."""

    def __init__(self, base_url: str = DITTO_URL, auth: tuple[str, str] = DITTO_AUTH):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.namespace = DITTO_NAMESPACE

    def _thing_id(self, asset_id: str) -> str:
        if ":" in asset_id:
            return asset_id
        return f"{self.namespace}:{asset_id}"

    async def upsert_thing(self, asset: dict[str, Any], client: httpx.AsyncClient | None = None) -> bool:
        """
        Create or update a Thing in Ditto.
        PUT /api/2/things/{thingId}
        """
        thing_id = self._thing_id(asset["asset_id"])
        body = {
            "policyId": thing_id,
            "attributes": {
                "asset_id": asset["asset_id"],
                "asset_type": asset["asset_type"],
                "name": asset.get("name", asset["asset_id"]),
                "parent": asset.get("parent"),
                "created_at": asset.get("created_at"),
            },
            "features": {
                "state": {
                    "properties": {
                        "value": asset.get("state", "unknown"),
                        "health": asset.get("health", "unknown"),
                    }
                },
                "risk": {
                    "properties": {
                        "score": float(asset.get("risk_score", 0.0) or 0.0),
                    }
                },
                "position": {
                    "properties": asset.get("position") or {},
                },
                "metrics": {
                    "properties": asset.get("metrics") or {},
                },
            },
        }

        async def _do_put(c: httpx.AsyncClient) -> bool:
            try:
                r = await c.put(
                    f"{self.base_url}/things/{thing_id}",
                    json=body,
                    headers=DITTO_HEADERS,
                )
                if r.status_code in (400, 404) and "policy" in r.text.lower():
                    body_no_policy = {k: v for k, v in body.items() if k != "policyId"}
                    r = await c.put(
                        f"{self.base_url}/things/{thing_id}",
                        json=body_no_policy,
                        headers=DITTO_HEADERS,
                    )
                r.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                logger.warning("Ditto upsert failed for %s: %s", thing_id, e.response.text[:200])
                return False
            except Exception as e:
                logger.warning("Ditto upsert error for %s: %s", thing_id, e)
                return False

        if client is not None:
            return await _do_put(client)

        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as c:
            return await _do_put(c)

    async def delete_thing(self, asset_id: str) -> bool:
        thing_id = self._thing_id(asset_id)
        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
            try:
                r = await client.delete(f"{self.base_url}/things/{thing_id}", headers=DITTO_HEADERS)
                return r.status_code in (204, 404)
            except Exception:
                return False

    async def get_thing(self, asset_id: str) -> dict[str, Any] | None:
        thing_id = self._thing_id(asset_id)
        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
            try:
                r = await client.get(f"{self.base_url}/things/{thing_id}", headers=DITTO_HEADERS)
                return r.json() if r.status_code == 200 else None
            except Exception:
                return None

    async def list_things(self, limit: int = 200) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(auth=self.auth, timeout=10.0) as client:
            try:
                r = await client.get(
                    f"{self.base_url}/search/things?option=size({limit})",
                    headers=DITTO_HEADERS,
                )
                if r.status_code == 200:
                    return r.json().get("items", [])
            except Exception:
                pass
        return []

    async def health(self) -> bool:
        """Check if Ditto is reachable."""
        async with httpx.AsyncClient(auth=self.auth, timeout=5.0) as client:
            try:
                r = await client.get(
                    f"{self.base_url}/search/things?option=size(1)",
                    headers=DITTO_HEADERS,
                )
                return r.status_code == 200
            except Exception:
                return False


ditto_adapter = DittoAdapter()
