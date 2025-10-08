from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr


class Settings(BaseSettings):
    APP_NAME: str = "mini-crm-ai"
    JWT_SECRET: str = "change-me"
    JWT_EXPIRES_MIN: int = 60 * 24

    DATABASE_URL: str = "sqlite:///./dev.db"
    REDIS_URL: str = "redis://redis:6379/0"

    MODEL_NAME: str = "t5-small"
    SUMMARY_MAX_TOKENS: int = 128

    # --- Admin bootstrap (optional) ---
    ADMIN_EMAIL: EmailStr | None = None
    ADMIN_PASSWORD: str | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> "Settings":
    return Settings()
