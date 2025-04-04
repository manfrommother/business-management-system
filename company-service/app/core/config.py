import os
from typing import List, Union, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core.core_schema import ValidationInfo

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_missing=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Company Administration Service"

    # Настройки базы данных PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "company_db"
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql+psycopg2://{info.data['POSTGRES_USER']}:{info.data['POSTGRES_PASSWORD']}"
            f"@{info.data['POSTGRES_SERVER']}:{info.data['POSTGRES_PORT']}/{info.data['POSTGRES_DB']}"
        )

    # Настройки Redis (если используется)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URI: Optional[str] = None

    @field_validator("REDIS_URI", mode="before")
    def assemble_redis_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        if isinstance(v, str):
            return v
        return f"redis://{info.data['REDIS_HOST']}:{info.data['REDIS_PORT']}/{info.data['REDIS_DB']}"

    # Настройки RabbitMQ (если используется)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URI: Optional[str] = None

    @field_validator("RABBITMQ_URI", mode="before")
    def assemble_rabbitmq_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        if isinstance(v, str):
            return v
        # Pika ожидает параметры отдельно, но URI может быть полезен для других целей
        return f"amqp://{info.data['RABBITMQ_USER']}:{info.data['RABBITMQ_PASSWORD']}@{info.data['RABBITMQ_HOST']}:{info.data['RABBITMQ_PORT']}{info.data['RABBITMQ_VHOST']}"


    # Настройки безопасности (например, для JWT)
    SECRET_KEY: str = "your-secret-key-here" # Обязательно измените и храните безопасно!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройки CORS (если необходим доступ из браузера)
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

# Создаем экземпляр настроек
settings = Settings() 