"""Application configuration, driven entirely by environment variables."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sentinel value. The app refuses to boot in production while this is in use.
DEFAULT_AUTH_SECRET = "dev-only-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/campusgig"
    auth_secret: str = DEFAULT_AUTH_SECRET
    frontend_url: str = "http://localhost:5173"
    api_v1_prefix: str = "/api/v1"

    # Institutional access
    allowed_email_domain: str = "thapar.edu"

    # Session
    session_cookie_name: str = "campusgig_session"
    session_ttl_minutes: int = 60 * 24 * 7

    # Login lockout
    login_max_failures: int = 10
    login_lockout_minutes: int = 15

    # Uploaded avatars and resumes
    media_root: str = "media"
    max_avatar_bytes: int = 2 * 1024 * 1024
    max_resume_bytes: int = 5 * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.is_production and self.auth_secret == DEFAULT_AUTH_SECRET:
            raise ValueError("AUTH_SECRET must be set to a unique value in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
