from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "AISTRUTH_DATABASE_URL"),
        description="asyncpg DSN, e.g. postgresql://user:pass@localhost:5432/aistruth",
    )
    barentswatch_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("BARENTSWATCH_CLIENT_ID"),
        description="OAuth client id from barentswatch.no MyPage (scope: ais).",
    )
    barentswatch_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("BARENTSWATCH_CLIENT_SECRET"),
        description="OAuth client secret (never commit; use env or secret store).",
    )
    cors_origins: str = Field(
        default="http://127.0.0.1:3000,http://localhost:3000",
        validation_alias=AliasChoices("AISTRUTH_CORS_ORIGINS"),
        description="Comma-separated origins for CORS (dev Next.js).",
    )
    api_keys: str = Field(
        default="",
        validation_alias=AliasChoices("AISTRUTH_API_KEYS"),
        description="Comma-separated API keys allowed to call /v1 routes. Empty disables auth.",
    )
    track_cache_ttl_seconds: int = Field(
        default=30,
        ge=0,
        validation_alias=AliasChoices("AISTRUTH_TRACK_CACHE_TTL"),
        description="In-process TTL for BarentsWatch track fetches. Set 0 to disable.",
    )
    geodnet_ntrip_user: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_NTRIP_USER"),
    )
    geodnet_ntrip_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_NTRIP_PASSWORD"),
    )
    geodnet_ntrip_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_NTRIP_HOST"),
    )
    geodnet_ntrip_port: int | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_NTRIP_PORT"),
    )
    geodnet_ntrip_mount: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_NTRIP_MOUNT"),
    )
    geodnet_smoke_lat: float = Field(
        default=59.6667,
        validation_alias=AliasChoices("GEODNET_SMOKE_LAT"),
        description="Default GGA latitude for NTRIP probes (decimal degrees).",
    )
    geodnet_smoke_lon: float = Field(
        default=10.6333,
        validation_alias=AliasChoices("GEODNET_SMOKE_LON"),
        description="Default GGA longitude for NTRIP probes (decimal degrees).",
    )
    enable_geodnet_debug_routes: bool = Field(
        default=False,
        validation_alias=AliasChoices("AISTRUTH_ENABLE_GEODNET_DEBUG"),
        description="If true, register GET /v1/debug/geodnet-ntrip (local/dev only).",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
