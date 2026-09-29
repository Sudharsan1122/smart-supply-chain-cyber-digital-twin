"""Reads Wazuh alerts from its API and POSTs to /api/events."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("uvicorn.error")


class WazuhAdapter:
    """Polls Wazuh Manager REST API (v4.7.0) and forwards security alerts."""

    def __init__(self):
        self.base = os.getenv("WAZUH_URL", "https://sscdt-wazuh:55000")
        self.auth = ("wazuh-wui", "MyS3cr37P450r.*-")
        self.api_events_url = os.getenv("INTERNAL_EVENTS_URL", "http://127.0.0.1:8000/api/events")
        self._seen_ids: set[str] = set()

    async def fetch_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Authenticate with Wazuh API, fetch recent alerts, and forward new ones to /api/events."""
        try:
            async with httpx.AsyncClient(auth=self.auth, verify=False, timeout=5.0) as c:
                r = await c.get(f"{self.base}/security/user/authenticate")
                token = None
                if r.status_code == 200:
                    data = r.json()
                    token = (data.get("data") or {}).get("token")

                headers = {"Authorization": f"Bearer {token}"} if token else {}
                alerts_resp = await c.get(
                    f"{self.base}/alerts?limit={limit}",
                    headers=headers,
                )
                if alerts_resp.status_code != 200:
                    return []

                items = (alerts_resp.json().get("data") or {}).get("affected_items") or []
                forwarded = []
                for item in items:
                    alert_id = str(item.get("id", ""))
                    if alert_id and alert_id in self._seen_ids:
                        continue
                    if alert_id:
                        self._seen_ids.add(alert_id)
                    event_payload = {
                        "asset_id": item.get("agent", {}).get("name", "VGW-101"),
                        "event_type": "wazuh_alert",
                        "severity": item.get("severity", "medium"),
                        "source": "wazuh",
                        "details": item,
                    }
                    try:
                        await c.post(self.api_events_url, json=event_payload, timeout=3.0)
                    except Exception:
                        pass
                    forwarded.append(event_payload)
                return forwarded
        except Exception as e:
            logger.debug("Wazuh poll skipped: %s", e)
            return []


wazuh_adapter = WazuhAdapter()


async def wazuh_sync_loop(interval: float = 30.0) -> None:
    """Background loop polling Wazuh Manager every 30s."""
    while True:
        try:
            await asyncio.sleep(interval)
            await wazuh_adapter.fetch_alerts(limit=20)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Wazuh sync warning: %s", e)
