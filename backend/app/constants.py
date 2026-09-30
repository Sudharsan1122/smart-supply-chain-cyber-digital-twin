"""Shared constants for Partner Data Sharing (CR-001) eliminating SonarQube S1192 string duplication."""
from __future__ import annotations


class PartnerConstants:
    """Domain constants for partner role, forecast modes, and commitment lifecycle statuses."""

    ROLE = "PARTNER"
    MODE_READ_ONLY = "read-only"
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REJECTED = "rejected"
    DEFAULT_REGION = "SOUTH"
    DEFAULT_PERIOD = "2026-W40"
    VALID_STATUSES = (STATUS_PENDING, STATUS_CONFIRMED, STATUS_REJECTED)
