from typing import List, Union
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Analytics Service"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    # Should be a list of strings, e.g., ["http://localhost:3000", "http://127.0.0.1:3000"]
    # Use environment variable like: BACKEND_CORS_ORIGINS='["http://localhost:3000"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    DATABASE_URL: PostgresDsn

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> RedisDsn:
        return RedisDsn(f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}")

    # RabbitMQ
    AMQP_URL: AmqpDsn

    # JWT Settings (should be same as other services)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery Settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Optional ClickHouse
    CLICKHOUSE_HOST: str | None = None
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_USER: str | None = None
    CLICKHOUSE_PASSWORD: str | None = None
    CLICKHOUSE_DB: str | None = None

    LOGGING_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings() 