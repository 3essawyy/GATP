"""Application settings, read from environment variables and `.env` (prefix ``GATP_``).

Every key is documented in `.env.example` at the repo root. Never commit real secrets.
"""

from functools import lru_cache
from pathlib import Path

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
    # Optional path to a Chromium binary. Only needed where Playwright's own browser download
    # is unavailable (e.g. a sandbox with a preinstalled Chromium). Empty = Playwright default.
    chromium_executable: str = ""

    # Storage (ADR-005): SQLite file + artifacts folder, both gitignored. Delete data/ to reset.
    data_dir: Path = Path("data")
    artifacts_dir: Path = Path("artifacts")
    database_url: str = ""  # default: sqlite:///<data_dir>/gatp.sqlite

    # Runner (ADR-004, ADR-017): typed jobs over a Unix socket; always headed except in CI.
    runner_socket: Path = Path("data/runner/runner.sock")
    runner_headless: bool = False
    runner_sandbox_dir: Path = Path("data/sandbox")
    runner_job_timeout_s: float = 60.0
    runner_slow_mo_ms: int = 0  # slow actions down so humans can follow the visible browser
    runner_isolation: str = "bwrap"  # bwrap | process (approved test runs, ADR-022)

    # LLM gateway (ADR-003, ADR-016). Providers: gemini | ollama | fake. Empty fallback = none.
    llm_primary: str = "gemini"
    llm_fallback: str = "ollama"
    llm_cache: bool = True
    llm_timeout_s: float = 120.0
    llm_max_retries: int = 2  # retries on rate limit / transient errors, per provider
    llm_backoff_s: float = 2.0  # first backoff; doubles each retry
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:3b"

    def resolved_database_url(self) -> str:
        """The SQLAlchemy URL, defaulting to a SQLite file inside ``data_dir``."""
        return self.database_url or f"sqlite:///{self.data_dir / 'gatp.sqlite'}"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings (cached; tests can call ``get_settings.cache_clear()``)."""
    return Settings()
