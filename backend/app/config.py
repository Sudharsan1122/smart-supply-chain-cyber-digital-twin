"""Environment configuration managed via pydantic-settings."""
from __future__ import annotations

import os
import secrets
from cryptography.fernet import Fernet
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_db_url() -> str:
    """Return environment database URL or in-memory SQLite fallback for local testing."""
    return os.getenv("DATABASE_URL", "sqlite:///./scdt_local.db")


def _default_redis_url() -> str:
    """Return environment Redis URL or local default."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _default_fernet_key() -> str:
    """Generate a valid URL-safe base64-encoded 32-byte key when not set in env."""
    env_val = os.getenv("FERNET_KEY")
    if env_val:
        return env_val
    return Fernet.generate_key().decode("utf-8")


class Settings(BaseSettings):
    """Application settings loaded strictly from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="Supply Chain Digital Twin")
    app_env: str = Field(default="development")
    database_url: str = Field(default_factory=_default_db_url)
    redis_url: str = Field(default_factory=_default_redis_url)
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    fernet_key: str = Field(default_factory=_default_fernet_key)
    audit_signing_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")
    reoptimize_threshold_pct: float = Field(default=5.0)
    partner_anonymization_k: int = Field(default=5)
    simulation_timeout_seconds: int = Field(default=25)

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a clean list."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
