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


@lru_cache
def get_settings() -> Settings:
    return Settings()
