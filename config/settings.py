"""Central application configuration."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Supply Chain Cyber Digital Twin"
    app_version: str = "1.0.0"
    environment: str = "DEBUG"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "supply_chain_twin"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_echo: bool = False
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_prefix: str = "supply_chain/telemetry"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    virustotal_api_key: str = ""
    abuseipdb_api_key: str = ""
    alienvault_otx_key: str = ""
    openweather_api_key: str = ""
    adapter_timeout_seconds: int = 15
    adapter_max_retries: int = 3
    adapter_backoff_factor: float = 0.5
    adapter_cache_ttl_seconds: int = 3600
    adapter_rate_limit_per_minute: int = 60
    external_apis_enabled: bool = True

    risk_weight_detections: float = 0.35
    risk_weight_transitions: float = 0.15
    risk_weight_incidents: float = 0.20
    risk_weight_threat_intel: float = 0.15
    risk_weight_centrality: float = 0.10
    risk_weight_health: float = 0.05
    risk_sweep_interval_seconds: int = 120
    risk_window_seconds: int = 3600

    triage_tp_threshold: float = 0.65
    triage_fp_threshold: float = 0.35
    triage_sweep_interval_seconds: int = 180
    triage_batch_size: int = 50

    ml_enabled: bool = True
    ml_artifacts_dir: str = "ml/artifacts"
    ml_feature_window_seconds: int = 60
    ml_min_samples_for_training: int = 200
    ml_contamination: float = 0.05

    enrichment_interval_seconds: int = 30
    enrichment_ttl_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url_async(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
