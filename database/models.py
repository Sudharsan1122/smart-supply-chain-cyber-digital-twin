"""SQLAlchemy 2.0 ORM models."""
from datetime import datetime

from sqlalchemy import (
    JSON, BigInteger, CheckConstraint, DateTime, Double, ForeignKey,
    Integer, Text, UniqueConstraint,
)
from sqlalchemy import String as VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class Telemetry(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    metric: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    value: Mapped[float | None] = mapped_column(Double, nullable=True)
    unit: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    source: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    severity: Mapped[str] = mapped_column(VARCHAR(16), default="info", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class TwinState(Base):
    __tablename__ = "twin_states"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    state: Mapped[str] = mapped_column(VARCHAR(32), default="unknown", nullable=False)
    health: Mapped[str] = mapped_column(VARCHAR(32), default="unknown", nullable=False)
    position: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class StateTransition(Base):
    __tablename__ = "state_transitions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    from_state: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    to_state: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    telemetry_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("telemetry.id", ondelete="SET NULL"), nullable=True)
    detection_type: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    severity: Mapped[str] = mapped_column(VARCHAR(16), default="medium", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Double, nullable=False)
    factors: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    model_version: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class AttackScenario(Base):
    __tablename__ = "attack_scenarios"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scenario_id: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_asset_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class AttackStory(Base):
    __tablename__ = "attack_stories"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    attack_id: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    scenario_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("attack_scenarios.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="open", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class IOC(Base):
    __tablename__ = "iocs"
    __table_args__ = (UniqueConstraint("value", "ioc_type", name="uq_iocs_value_type"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(VARCHAR(512), nullable=False)
    ioc_type: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    source: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class IOCEnrichment(Base):
    __tablename__ = "ioc_enrichments"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ioc_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("iocs.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    verdict: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    enriched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class BlastRadius(Base):
    __tablename__ = "blast_radius"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    attack_story_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("attack_stories.id", ondelete="CASCADE"), nullable=True)
    source_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    impacted_asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    impact_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    path: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class Triage(Base):
    __tablename__ = "triage"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    detection_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)
    verdict: Mapped[str] = mapped_column(VARCHAR(4), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    analyst: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_uid: Mapped[str] = mapped_column(VARCHAR(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)
    severity: Mapped[str] = mapped_column(VARCHAR(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="open", nullable=False)
    root_asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    rule_id: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class IncidentMember(Base):
    __tablename__ = "incident_members"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    incident_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    telemetry_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("telemetry.id", ondelete="CASCADE"), nullable=True)
    event_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=True)
    role: Mapped[str] = mapped_column(VARCHAR(32), default="evidence", nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class TwinStateSnapshot(Base):
    __tablename__ = "twin_state_snapshots"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(VARCHAR(8), nullable=False)
    state: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    health: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    position: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics_full: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics_patch: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    transition_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class TransitionAnomaly(Base):
    __tablename__ = "transition_anomalies"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    transition_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("state_transitions.id", ondelete="SET NULL"), nullable=True)
    machine: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    from_state: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    to_state: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    reason: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)
    severity: Mapped[str] = mapped_column(VARCHAR(16), default="medium", nullable=False)
    kind: Mapped[str] = mapped_column(VARCHAR(32), default="invalid_transition", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class AttackStoryEvent(Base):
    __tablename__ = "attack_story_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("attack_stories.id", ondelete="CASCADE"), nullable=False)
    evidence_kind: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    evidence_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    title: Mapped[str] = mapped_column(VARCHAR(256), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tactic: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class AttackStoryTactic(Base):
    __tablename__ = "attack_story_tactics"
    __table_args__ = (UniqueConstraint("story_id", "tactic", name="uq_story_tactic"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("attack_stories.id", ondelete="CASCADE"), nullable=False)
    tactic: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Double, nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)


class IOCObservation(Base):
    __tablename__ = "ioc_observations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ioc_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("iocs.id", ondelete="CASCADE"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    attack_story_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("attack_stories.id", ondelete="SET NULL"), nullable=True)
    evidence_kind: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    evidence_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)
    occurrences: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
