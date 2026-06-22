"""
FastAPI Configuration
=====================
All settings loaded from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Cryptrix"
    VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Postgres
    DATABASE_URL: str = "postgresql+asyncpg://cryptrix_admin:cryptrix_password@localhost:5432/cryptrix_db"

    # Redis
    REDIS_URL: str = "redis://:redis_password@localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    # API
    API_PREFIX: str = "/api/v1"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"


settings = Settings()
