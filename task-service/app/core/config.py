# task-service/app/core/config.py
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
    PROJECT_NAME: str = "Task Management Service"

    # Настройки базы данных PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "task_db" # База данных для задач
    DATABASE_URI: Optional[str] = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        if isinstance(v, str):
            return v
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        server = info.data.get("POSTGRES_SERVER")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")
        return f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"

    # Настройки безопасности (JWT)
    SECRET_KEY: str = "your_very_strong_and_secret_random_key_for_tasks_here" # Обязательно измените через .env!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройки CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Optional[Union[str, List[str]]]) -> Union[List[str], str]:
        if isinstance(v, str) and v:
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return [] # Возвращаем пустой список по умолчанию

    # Локальное хранилище файлов
    UPLOAD_DIRECTORY: str = "./uploads" # Путь относительно корня проекта

    # Настройки RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    # URI для информации, pika обычно использует отдельные параметры
    RABBITMQ_URI: Optional[str] = None
    RABBITMQ_EXCHANGE_NAME: str = "task_events" # Имя обменника для событий задач

    @field_validator("RABBITMQ_URI", mode="before")
    def assemble_rabbitmq_connection(
        cls, v: Optional[str], info: ValidationInfo
    ) -> str:
        if isinstance(v, str):
            return v
        user = info.data.get("RABBITMQ_USER")
        password = info.data.get("RABBITMQ_PASSWORD")
        host = info.data.get("RABBITMQ_HOST")
        port = info.data.get("RABBITMQ_PORT")
        vhost = info.data.get("RABBITMQ_VHOST", "/")
        # Убедимся, что vhost начинается с /
        if not vhost.startswith("/"):
             vhost = "/" + vhost
        return f"amqp://{user}:{password}@{host}:{port}{vhost}"

# Создаем экземпляр настроек
settings = Settings() 