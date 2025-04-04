import os
from pydantic import BaseSettings, PostgresDsn, validator
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "User Service"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    REDIS_HOST: str
    REDIS_PORT: str = "6379"
    
    RABBITMQ_HOST: str
    RABBITMQ_PORT: str = "5672"
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    ACCOUNT_DELETION_DAYS: int = 30
    
    # Настройки email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()