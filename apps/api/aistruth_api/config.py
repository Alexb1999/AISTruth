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
    ais_source: str = Field(
        default="barentswatch",
        validation_alias=AliasChoices("AISTRUTH_AIS_SOURCE"),
        description="AIS adapter selection: barentswatch, spire, or file.",
    )
    spire_api_key: str | None = Field(default=None, validation_alias=AliasChoices("SPIRE_API_KEY"))
    spire_base_url: str = Field(
        default="https://api.spire.com",
        validation_alias=AliasChoices("SPIRE_BASE_URL"),
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
    geodnet_rtk_app_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_RTK_APP_ID"),
        description="Enterprise RTK REST API appId (station list / coverage).",
    )
    geodnet_rtk_app_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_RTK_APP_KEY"),
        description="Enterprise RTK REST API appKey (secret; never commit).",
    )
    geodnet_rtk_api_base: str = Field(
        default="https://rtk.geodnet.com",
        validation_alias=AliasChoices("GEODNET_RTK_API_BASE"),
        description="Base URL for GEODNET RTK REST API (no trailing slash).",
    )
    geodnet_rtk_station_region: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEODNET_RTK_STATION_REGION"),
        description=(
            "Optional ISO 3166-1 alpha-3 filter for POST /api/v3/station/list (e.g. NOR, USA)."
        ),
    )
    geodnet_sync_stations_at_startup: bool = Field(
        default=False,
        validation_alias=AliasChoices("GEODNET_SYNC_STATIONS_AT_STARTUP"),
        description=(
            "If true and RTK API credentials + DATABASE_URL are set, sync stations once at boot."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
