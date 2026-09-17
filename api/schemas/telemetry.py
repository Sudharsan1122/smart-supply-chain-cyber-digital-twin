"""Telemetry Pydantic schemas."""
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AssetType = Literal[
    "TRUCK", "WAREHOUSE", "SENSOR", "VEHICLE_GATEWAY",
    "API_GATEWAY", "APPLICATION", "AUTH_SYSTEM", "DATABASE", "SUPPLIER",
]


class GPSData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class TelemetryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(..., min_length=1, max_length=64)
    asset_type: AssetType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    gps: GPSData | None = None
    speed: float | None = Field(None, ge=0, le=200)
    direction: str | None = None
    fuel: float | None = Field(None, ge=0, le=100)
    battery: float | None = Field(None, ge=0, le=100)
    temperature: float | None = Field(None, ge=-50, le=100)
    humidity: float | None = Field(None, ge=0, le=100)
    status: str | None = None
    firmware: str | None = None
    network_destinations: list[str] = Field(default_factory=list)
    auth_events: int = Field(0, ge=0)
    failed_logins: int = Field(0, ge=0)
    api_calls: int = Field(0, ge=0)
    unusual_api_calls: int = Field(0, ge=0)
    sensor_type: str | None = None
    door_status: str | None = None
    occupancy: int | None = Field(None, ge=0)
    power_consumption: float | None = Field(None, ge=0)
    raw: dict[str, Any] | None = None

    @field_validator("asset_id")
    @classmethod
    def _check_prefix(cls, v: str) -> str:
        valid = ("TRUCK-", "WH-", "VGW-", "TEMP-", "HUM-", "DOOR-",
                 "API-GW-", "APP-", "AUTH-", "DB-", "SUP-")
        if not any(v.startswith(p) for p in valid):
            raise ValueError(f"asset_id must start with one of {valid}")
        return v


class TelemetryResponse(BaseModel):
    success: bool
    telemetry_id: int | None = None
    asset_id: str
    timestamp: datetime
    message: str
    twin_state: dict[str, Any] | None = None
