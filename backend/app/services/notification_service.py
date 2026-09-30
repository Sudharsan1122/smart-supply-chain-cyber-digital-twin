"""Notification service subscribing to supply chain domain events."""
from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.services.audit_service import event_bus

logger = logging.getLogger(__name__)
_notifications: list[dict[str, Any]] = []


def dispatch_notification(channel: str, subject: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Record and dispatch an operational notification to planners or partners.

    Args:
        channel: Notification channel identifier (e.g., 'PLANNER_ALERT', 'PARTNER_WEBHOOK').
        subject: Human-readable alert title.
        payload: Structured metadata dictionary.

    Returns:
        Dispatched notification envelope.
    """
    envelope = {"channel": channel, "subject": subject, "payload": payload}
    _notifications.append(envelope)
    logger.info("Notification dispatched [%s]: %s", channel, subject)
    return envelope


def list_recent_notifications(limit: int = 25) -> list[dict[str, Any]]:
    """Return the most recent dispatched notifications."""
    return list(reversed(_notifications[-limit:]))


def _notification_event_listener(_db: Session, event: dict[str, Any]) -> None:
    """Subscribe to critical EventBus events and emit planner notifications."""
    action = str(event.get("action", ""))
    if action in {"AUTO_REOPTIMIZE_TRIGGERED", "PARTNER_COMMITMENT_CONFIRMED", "SIMULATION_COMPLETED"}:
        dispatch_notification(
            channel="OPERATIONS_BUS",
            subject=f"Event: {action} on {event.get('resource', 'NETWORK')}",
            payload=event.get("details", {}),
        )


event_bus.subscribe(_notification_event_listener)
