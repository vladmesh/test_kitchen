from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development")
    api_debug: bool = Field(default=False)

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/mini_crm", alias="DATABASE_URL"
    )
    sync_database_url: str | None = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/mini_crm",
        alias="SYNC_DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    jwt_secret_key: str = Field(default="changeme", alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(default="changeme-refresh", alias="JWT_REFRESH_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 30, alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )

    first_superuser_email: str | None = Field(default=None, alias="FIRST_SUPERUSER_EMAIL")
    first_superuser_password: str | None = Field(default=None, alias="FIRST_SUPERUSER_PASSWORD")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    analytics_cache_ttl_seconds: int = Field(default=60, alias="ANALYTICS_CACHE_TTL_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()
