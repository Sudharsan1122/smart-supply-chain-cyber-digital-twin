"""Domain-specific exceptions for Partner Data Sharing (CR-001), resolving SonarQube S112."""
from __future__ import annotations


class InvalidCommitmentError(ValueError):
    """Raised when a partner capacity commitment has invalid period bounds or non-positive capacity."""


class CommitmentReplayError(FileExistsError):
    """Raised when a duplicate commitment nonce is submitted (replay attack attempt)."""
