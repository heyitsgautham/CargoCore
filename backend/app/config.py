from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore docker-compose-only vars (POSTGRES_USER, etc.)
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440  # 24 hours — suits long driver shifts
    refresh_token_expire_days: int = 7

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://logistics_user:logistics_pass@localhost:5432/logistics_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Google APIs ───────────────────────────────────────────────────────────
    google_client_id: str = ""
    google_maps_api_key: str = ""
    gemini_api_key: str = ""

    # ── Daily.co Video Conferencing ───────────────────────────────────────────
    daily_api_key: str = ""

    # ── File Storage ──────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    # ── Email / SMS ───────────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    # One JSON object per line when true; defaults to true when APP_ENV=production.
    log_json: bool | None = None

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("log_json", mode="before")
    @classmethod
    def _blank_log_json_means_unset(cls, value):
        # `LOG_JSON=` in an .env file should follow APP_ENV, not fail startup.
        return None if isinstance(value, str) and not value.strip() else value

    @property
    def log_json_enabled(self) -> bool:
        return self.is_production if self.log_json is None else self.log_json


@lru_cache
def get_settings() -> Settings:
    return Settings()
