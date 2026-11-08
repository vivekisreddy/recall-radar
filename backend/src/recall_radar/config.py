"""App settings, read from environment variables (or a .env file in development)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads the repo-root .env when run from backend/ (later files win).
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://recall:recall@localhost:5432/recall_radar"
    redis_url: str = "redis://localhost:6379/0"

    # Comma-separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000"

    # Optional: raises openFDA's daily request limit. https://open.fda.gov/apis/authentication/
    openfda_api_key: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
