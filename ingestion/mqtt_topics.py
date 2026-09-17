"""Phase 6 - MQTT topic parsing."""
from dataclasses import dataclass
from config.settings import settings


@dataclass
class ParsedTopic:
    kind: str
    asset_id: str | None


def parse_topic(topic: str) -> ParsedTopic:
    prefix = settings.mqtt_topic_prefix.rstrip("/")
    if not topic.startswith(prefix + "/"):
        return ParsedTopic(kind="unknown", asset_id=None)
    rest = topic[len(prefix) + 1:]
    parts = rest.split("/")
    if len(parts) == 1 and parts[0] == "status":
        return ParsedTopic(kind="status", asset_id=None)
    if len(parts) == 2:
        kind = parts[0]
        asset_id = parts[1]
        if kind == "telemetry":
            return ParsedTopic(kind="telemetry", asset_id=asset_id)
        if kind == "events":
            return ParsedTopic(kind="event", asset_id=asset_id)
    return ParsedTopic(kind="unknown", asset_id=None)


def subscription_patterns() -> list[tuple[str, int]]:
    prefix = settings.mqtt_topic_prefix.rstrip("/")
    return [
        (f"{prefix}/telemetry/+", 1),
        (f"{prefix}/events/+", 1),
        (f"{prefix}/status", 0),
    ]
