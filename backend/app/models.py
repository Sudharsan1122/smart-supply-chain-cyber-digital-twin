"""SQLAlchemy 2.0 ORM models for the Supply Chain Digital Twin."""
from __future__ import annotations

from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security import RoleEnum


def _utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    """Application user account supporting RBAC and partner org scoping."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default=RoleEnum.VIEWER.value)
    org_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="SOUTH")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class SupplyNode(Base):
    """Physical or logical supply chain network node (Supplier, Factory, Warehouse, Port, Retailer)."""

    __tablename__ = "supply_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, default="SOUTH", index=True)
    capacity: Mapped[float] = mapped_column(Float, nullable=False, default=1000.0)
    fixed_cost: Mapped[float] = mapped_column(Float, nullable=False, default=5000.0)
    inventory: Mapped[float] = mapped_column(Float, nullable=False, default=500.0)
    demand: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    org_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class SupplyEdge(Base):
    """Directed transportation lane connecting two supply chain nodes."""

    __tablename__ = "supply_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    edge_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    source_node_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_node_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    lead_time_days: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=4.5)
    max_flow: Mapped[float] = mapped_column(Float, nullable=False, default=800.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SimulationRun(Base):
    """Historical record of a what-if disruption simulation execution."""

    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_node_code: Mapped[str] = mapped_column(String(32), nullable=False)
    severity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    service_level_pct: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    unmet_demand: Mapped[float] = mapped_column(Float, nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class OptimizationRun(Base):
    """Record of a MILP facility location and flow allocation optimization."""

    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trigger_reason: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    objective_cost: Mapped[float] = mapped_column(Float, nullable=False)
    open_facilities_json: Mapped[str] = mapped_column(Text, nullable=False)
    flow_allocations_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class AuditLog(Base):
    """Append-only, hash-chained, HMAC-SHA256 signed security and operational audit record."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class CommitmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class PartnerOrganization(Base):
    __tablename__ = "partner_organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    org_id = Column(String(40), nullable=False, unique=True, index=True)
    region = Column(String(80), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=_utc_now)
    commitments = relationship("PartnerCommitment", back_populates="partner")


class PartnerCommitment(Base):
    __tablename__ = "partner_commitments"
    id = Column(Integer, primary_key=True)
    partner_org_id = Column(Integer, ForeignKey("partner_organizations.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    committed_capacity = Column(Numeric(12, 2), nullable=False)
    signature = Column(String(128), nullable=False)
    nonce = Column(String(64), nullable=False, unique=True)
    status = Column(
        SQLEnum(CommitmentStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        default=CommitmentStatus.PENDING.value,
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=_utc_now)
    partner = relationship("PartnerOrganization", back_populates="commitments")
