from typing import List
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Model Configurations
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Environment Settings
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Cryptrix"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "cryptrix_jwt_signing_secret_key_change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520

    # PostgreSQL Connections
    DATABASE_URL: str = "postgresql+asyncpg://cryptrix_admin:cryptrix_secure_password_123@localhost:5432/cryptrix_app"

    # Redis Cache Connections
    REDIS_URL: str = "redis://:redis_secure_password_123@localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_secure_password_123"

    # CORS Allowed Hosts
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # MLflow Configs
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "cryptrix-market-forecasting"

    # Future Broker Configs (Kafka Placeholders)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_MARKET_TICKERS: str = "cryptrix.market.tickers"
    KAFKA_TOPIC_PREDICTIONS: str = "cryptrix.ml.predictions"
    KAFKA_TOPIC_WHALE_ALERTS: str = "cryptrix.chain.whales"

# Singleton instance of settings across backend services
settings = Settings()
