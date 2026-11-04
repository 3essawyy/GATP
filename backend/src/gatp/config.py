"""Application settings, read from environment variables and `.env` (prefix ``GATP_``).

Every key is documented in `.env.example` at the repo root. Never commit real secrets.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings shared by the API and the runner."""

    model_config = SettingsConfigDict(
        env_prefix="GATP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings (cached; tests can call ``get_settings.cache_clear()``)."""
    return Settings()
