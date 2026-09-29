"""Reads Suricata eve.json and POSTs alerts to /api/events."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("uvicorn.error")


class SuricataAdapter:
    """Tails Suricata eve.json log file and forwards IDS alerts to /api/events."""

    def __init__(self, eve_path: str | Path = "/var/log/suricata/eve.json"):
        self.eve_path = Path(eve_path)
        self.api_events_url = os.getenv("INTERNAL_EVENTS_URL", "http://127.0.0.1:8000/api/events")
        self._offset: int = 0

    def tail_alerts(self) -> list[dict[str, Any]]:
        """Read newly appended lines from eve.json and transform alert events."""
        if not self.eve_path.exists():
            return []
        alerts: list[dict[str, Any]] = []
        try:
            with self.eve_path.open("r", encoding="utf-8") as f:
                f.seek(self._offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("event_type") == "alert":
                        alerts.append({
                            "asset_id": rec.get("asset_id", "API-GW-001"),
                            "event_type": "suricata_alert",
                            "severity": rec.get("severity_label", "high"),
                            "source": "suricata",
                            "details": rec,
                        })
                self._offset = f.tell()
        except Exception as e:
            logger.debug("Suricata tail error: %s", e)
        return alerts

    async def forward_new_alerts(self) -> int:
        alerts = self.tail_alerts()
        if not alerts:
            return 0
        sent = 0
        async with httpx.AsyncClient(timeout=3.0) as client:
            for ev in alerts:
                try:
                    await client.post(self.api_events_url, json=ev)
                    sent += 1
                except Exception:
                    pass
        return sent


suricata_adapter = SuricataAdapter()


async def suricata_sync_loop(interval: float = 15.0) -> None:
    """Background loop tailing Suricata eve.json every 15s."""
    while True:
        try:
            await asyncio.sleep(interval)
            await suricata_adapter.forward_new_alerts()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("Suricata sync warning: %s", e)
