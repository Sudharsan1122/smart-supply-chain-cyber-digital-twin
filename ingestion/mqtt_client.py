"""Phase 6 - MQTT bridge."""
from __future__ import annotations
import asyncio
import json
import logging

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from api.schemas.events import EventPayload
from api.schemas.telemetry import TelemetryPayload
from config.settings import settings
from database.db import AsyncSessionLocal
from ingestion.mqtt_topics import parse_topic, subscription_patterns
from ingestion.pipeline import ingest_event, ingest_telemetry

logger = logging.getLogger(__name__)


class MQTTBridge:
    def __init__(self):
        self.client: mqtt.Client | None = None
        self.loop = None
        self._connected = False
        self._stats = {"received": 0, "ingested": 0, "rejected_parse": 0,
                       "rejected_validation": 0, "ingest_errors": 0}

    def start(self, loop):
        if self.client is not None:
            return
        self.loop = loop
        client = mqtt.Client(
            client_id=f"sscdt-bridge-{id(self)}",
            protocol=mqtt.MQTTv311, clean_session=True,
        )
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        self.client = client
        try:
            client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, keepalive=60)
            client.loop_start()
            logger.info("MQTT bridge connecting to %s:%d",
                        settings.mqtt_broker_host, settings.mqtt_broker_port)
        except Exception as e:
            logger.warning("MQTT connect failed: %s", e)
            self.client = None

    def stop(self):
        if self.client is None:
            return
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        finally:
            self.client = None
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def status(self) -> dict:
        return {
            "connected": self._connected,
            "broker": f"{settings.mqtt_broker_host}:{settings.mqtt_broker_port}",
            "topic_prefix": settings.mqtt_topic_prefix,
            "subscriptions": [t for t, _ in subscription_patterns()],
            "stats": dict(self._stats),
        }

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("MQTT connected")
            for topic, qos in subscription_patterns():
                client.subscribe(topic, qos=qos)
        else:
            self._connected = False

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        if self.loop is None:
            return
        self._stats["received"] += 1
        asyncio.run_coroutine_threadsafe(
            self._handle_message(msg.topic, msg.payload), self.loop
        )

    async def _handle_message(self, topic: str, payload_bytes: bytes) -> None:
        parsed = parse_topic(topic)
        if parsed.kind in ("unknown", "status"):
            return
        try:
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            self._stats["rejected_parse"] += 1
            return
        data.setdefault("asset_id", parsed.asset_id)
        try:
            if parsed.kind == "telemetry":
                payload = TelemetryPayload(**data)
                async with AsyncSessionLocal() as session:
                    await ingest_telemetry(session, payload)
            elif parsed.kind == "event":
                payload = EventPayload(**data)
                async with AsyncSessionLocal() as session:
                    await ingest_event(session, payload)
        except ValidationError:
            self._stats["rejected_validation"] += 1
            return
        except Exception as e:
            self._stats["ingest_errors"] += 1
            logger.error("Ingest failed on %s: %s", topic, e)
            return
        self._stats["ingested"] += 1


mqtt_bridge = MQTTBridge()
