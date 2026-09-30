"""Event-bus subscriber and append-only HMAC-SHA256 hash-chained audit logging service."""
from __future__ import annotations

from collections.abc import Callable
import hashlib
import hmac
import json
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuditLog

logger = logging.getLogger(__name__)
GENESIS_HASH = "0" * 64


class EventBus:
    """Lightweight publish-subscribe event bus decoupling domain modules from audit/notification sinks."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[Session, dict[str, Any]], None]] = []

    def subscribe(self, callback: Callable[[Session, dict[str, Any]], None]) -> None:
        """Register an event subscriber callback."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def publish(self, db: Session, event: dict[str, Any]) -> None:
        """Publish an event to all registered subscribers."""
        for subscriber in self._subscribers:
            subscriber(db, event)


event_bus = EventBus()


def compute_audit_signature(prev_hash: str, actor: str, action: str, resource: str, details_json: str) -> str:
    """Compute an HMAC-SHA256 signature chaining the previous record's signature.

    Args:
        prev_hash: Signature of the immediately preceding AuditLog row.
        actor: Username or system principal.
        action: Action identifier.
        resource: Target entity identifier.
        details_json: Canonical JSON string of event metadata.

    Returns:
        Hex-encoded HMAC-SHA256 digest.
    """
    message = f"{prev_hash}|{actor}|{action}|{resource}|{details_json}".encode("utf-8")
    key = settings.audit_signing_key.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def record_audit_event(db: Session, event: dict[str, Any]) -> AuditLog:
    """Persist an append-only, cryptographically chained audit event.

    Args:
        db: Active SQLAlchemy session.
        event: Event dictionary containing actor, action, resource, and details.

    Returns:
        Newly persisted AuditLog ORM instance.
    """
    last_entry = db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).scalar_one_or_none()
    prev_hash = last_entry.signature if last_entry else GENESIS_HASH
    actor = str(event.get("actor", "SYSTEM"))
    action = str(event.get("action", "STATE_CHANGE"))
    resource = str(event.get("resource", "NETWORK"))
    details_json = json.dumps(event.get("details", {}), sort_keys=True)
    signature = compute_audit_signature(prev_hash, actor, action, resource, details_json)
    entry = AuditLog(
        actor=actor,
        action=action,
        resource=resource,
        details_json=details_json,
        prev_hash=prev_hash,
        signature=signature,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_audit_chain(db: Session) -> bool:
    """Verify integrity of the entire hash-chained audit log.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        True if all HMAC signatures and chain links are intact, False otherwise.
    """
    entries = list(db.execute(select(AuditLog).order_by(AuditLog.id.asc())).scalars().all())
    prev_hash = GENESIS_HASH
    for item in entries:
        expected = compute_audit_signature(prev_hash, item.actor, item.action, item.resource, item.details_json)
        if not hmac.compare_digest(expected, item.signature) or item.prev_hash != prev_hash:
            return False
        prev_hash = item.signature
    return True


def _audit_subscriber(db: Session, event: dict[str, Any]) -> None:
    """Internal event-bus handler that writes domain events to the audit log."""
    record_audit_event(db, event)


event_bus.subscribe(_audit_subscriber)
