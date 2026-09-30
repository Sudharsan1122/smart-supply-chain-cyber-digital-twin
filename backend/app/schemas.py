"""Pydantic v2 Data Transfer Objects (DTOs) with strict input validation."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security import RoleEnum


class NodeTypeEnum(StrEnum):
    """Valid supply chain node categories."""

    SUPPLIER = "SUPPLIER"
    FACTORY = "FACTORY"
    WAREHOUSE = "WAREHOUSE"
    PORT = "PORT"
    RETAILER = "RETAILER"


class ScenarioTypeEnum(StrEnum):
    """Supported what-if disruption scenario types."""

    SUPPLIER_FAILURE = "SUPPLIER_FAILURE"
    DEMAND_SPIKE = "DEMAND_SPIKE"
    PORT_CLOSURE = "PORT_CLOSURE"


class UserCreate(BaseModel):
    """Request schema for registering a user."""

    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum = Field(default=RoleEnum.VIEWER)
    org_id: str | None = Field(default=None, max_length=64, pattern=r"^[a-zA-Z0-9_-]*$")


class LoginRequest(BaseModel):
    """Credentials payload for JWT login."""

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    """Payload for rotating a refresh token."""

    refresh_token: str = Field(min_length=16)


class TokenResponse(BaseModel):
    """JWT access and refresh token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    org_id: str | None = None


class SupplyNodeCreate(BaseModel):
    """Validated payload for creating or updating a supply chain node."""

    node_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    name: str = Field(min_length=2, max_length=128)
    node_type: NodeTypeEnum
    region: str = Field(default="SOUTH", max_length=64)
    capacity: float = Field(ge=0.0, le=1_000_000.0)
    fixed_cost: float = Field(ge=0.0, le=10_000_000.0)
    inventory: float = Field(ge=0.0, le=1_000_000.0)
    demand: float = Field(ge=0.0, le=1_000_000.0)
    is_open: bool = True
    org_id: str | None = Field(default=None, max_length=64)


class SupplyNodeRead(SupplyNodeCreate):
    """Serialized supply chain node representation."""

    model_config = ConfigDict(from_attributes=True)
    id: int


class SupplyEdgeCreate(BaseModel):
    """Validated payload for creating or updating a transportation lane."""

    edge_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    source_node_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    target_node_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    lead_time_days: float = Field(gt=0.0, le=365.0)
    unit_cost: float = Field(ge=0.0, le=100_000.0)
    max_flow: float = Field(ge=0.0, le=1_000_000.0)
    is_active: bool = True


class SupplyEdgeRead(SupplyEdgeCreate):
    """Serialized transportation edge representation."""

    model_config = ConfigDict(from_attributes=True)
    id: int


class TelemetrySyncPayload(BaseModel):
    """Real-time telemetry update for a node triggering bidirectional sync and >5% drift checks."""

    node_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    inventory: float | None = Field(default=None, ge=0.0, le=1_000_000.0)
    demand: float | None = Field(default=None, ge=0.0, le=1_000_000.0)
    capacity: float | None = Field(default=None, ge=0.0, le=1_000_000.0)


class SimulationRequest(BaseModel):
    """Input parameters for running an isolated what-if disruption simulation."""

    scenario_type: ScenarioTypeEnum
    target_node_code: str = Field(min_length=3, max_length=32, pattern=r"^[A-Z0-9-]+$")
    severity_pct: float = Field(gt=0.0, le=100.0, default=50.0)
    duration_days: int = Field(ge=1, le=180, default=14)


class SimulationResponse(BaseModel):
    """Simulation execution output metrics."""

    id: int
    scenario_type: str
    target_node_code: str
    severity_pct: float
    duration_days: int
    status: str
    service_level_pct: float
    total_cost: float
    unmet_demand: float
    recommendations: list[str]


class OptimizationRequest(BaseModel):
    """Parameters for triggering a MILP network optimization."""

    trigger_reason: str = Field(default="MANUAL_PLANNER_REQUEST", max_length=128)
    demand_multiplier: float = Field(default=1.0, gt=0.1, le=5.0)


class OptimizationResponse(BaseModel):
    """MILP optimization result with open facilities and flow allocations."""

    id: int
    trigger_reason: str
    status: str
    objective_cost: float
    open_facilities: list[str]
    flow_allocations: dict[str, float]


class AuditLogRead(BaseModel):
    """Serialized signed audit log entry."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    actor: str
    action: str
    resource: str
    details_json: str
    prev_hash: str
    signature: str
    created_at: datetime


class PartnerForecastResponse(BaseModel):
    region: str
    period: str
    aggregated_demand: float
    k_level: int


class CommitmentCreate(BaseModel):
    period_start: datetime
    period_end: datetime
    committed_capacity: Decimal = Field(gt=0)
    nonce: str | None = Field(default=None)

    @field_validator("period_end")
    @classmethod
    def end_after_start(cls, v: datetime, info: object) -> datetime:
        data = getattr(info, "data", {})
        if "period_start" in data and v <= data["period_start"]:
            raise ValueError("period_end must be after period_start")
        return v


class CommitmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    signature: str
    created_at: datetime
