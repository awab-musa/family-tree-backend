"""
Application configuration loaded from environment variables.
Uses pydantic-settings so values are validated at startup (fail fast on Lambda cold start).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- App ----
    APP_NAME: str = "Family Tree API"
    ENV: str = "development"  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"

    # ---- Database (Amazon RDS - PostgreSQL) ----
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@host:5432/family_tree
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5

    # ---- JWT Auth ----
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ---- AWS / S3 ----
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    S3_PRESIGNED_URL_EXPIRE_SECONDS: int = 3600

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - safe to reuse across a warm Lambda container."""
    return Settings()


settings = get_settings()