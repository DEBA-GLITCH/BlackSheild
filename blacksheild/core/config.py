
# Centralized configuration for BlackSheild.
#
# All settings are loaded from environment variables (via .env in development).
# Pydantic-settings validates types at startup so misconfiguration fails fast,
# not mid-run when an API call is made.
#
# Pattern: import the `settings` singleton anywhere in the codebase.
# Never read os.environ directly outside this file.

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All BlackSheild runtime configuration.

    Fields without defaults are required - the app will not start without them.
    Fields with defaults are optional but recommended.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Do not raise on extra fields from .env - keeps things future-proof
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LangSmith / LangChain tracing
    # ------------------------------------------------------------------
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="blacksheild", alias="LANGCHAIN_PROJECT")

    # ------------------------------------------------------------------
    # External API keys
    # ------------------------------------------------------------------
    nvd_api_key: str | None = Field(default=None, alias="NVD_API_KEY")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    # OSV has no auth requirement

    # ------------------------------------------------------------------
    # Chroma vector store
    # ------------------------------------------------------------------
    chroma_mode: str = Field(default="local", alias="CHROMA_MODE")
    chroma_persist_dir: str = Field(default="./chroma_store", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(
        default="blacksheild_findings", alias="CHROMA_COLLECTION_NAME"
    )

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------
    idempotency_ttl_hours: int = Field(default=24, alias="IDEMPOTENCY_TTL_HOURS")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    env: str = Field(default="development", alias="ENV")

    # ------------------------------------------------------------------
    # HTTP client timeouts (seconds) - not in .env, these are tuned constants
    # ------------------------------------------------------------------
    http_connect_timeout: float = 10.0
    http_read_timeout: float = 30.0
    http_total_timeout: float = 60.0

    # ------------------------------------------------------------------
    # Retry policy defaults (used by Tenacity in Phase 2)
    # ------------------------------------------------------------------
    retry_max_attempts: int = 3
    retry_wait_min_seconds: float = 1.0
    retry_wait_max_seconds: float = 10.0

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got: {v}")
        return upper

    @field_validator("chroma_mode")
    @classmethod
    def validate_chroma_mode(cls, v: str) -> str:
        allowed = {"local", "remote"}
        if v.lower() not in allowed:
            raise ValueError(f"chroma_mode must be one of {allowed}, got: {v}")
        return v.lower()

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"env must be one of {allowed}, got: {v}")
        return v.lower()

    def is_production(self) -> bool:
        return self.env == "production"

    def nvd_has_key(self) -> bool:
        """NVD works without a key but rate limits are severe without one."""
        return self.nvd_api_key is not None

    def github_has_token(self) -> bool:
        return self.github_token is not None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings singleton.

    lru_cache means .env is only read once per process.
    In tests, call get_settings.cache_clear() before patching environment vars.
    """
    return Settings()


# Module-level singleton for convenient import.
# Usage anywhere in the codebase:
#   from blacksheild.core.config import settings
settings = get_settings()