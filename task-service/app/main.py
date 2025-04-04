# task-service/app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import engine
# Импортируем Base, чтобы создать таблицы
from app.db.base_class import Base
# Импортируем функции для RabbitMQ
from app.core.messaging import get_rabbitmq_connection, close_rabbitmq_connection

# Импортируем и подключаем api_router
from app.api.v1.api import api_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up {settings.PROJECT_NAME}...")
    logger.info("Creating database tables (dev mode)...")
    try:
        # Импортируем модели здесь (или в app.db.__init__), чтобы Base их знала
        # import app.models # noqa
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    # 2. Подключение к RabbitMQ
    logger.info("Connecting to RabbitMQ...")
    if get_rabbitmq_connection(): # Попытка установить соединение
        logger.info("RabbitMQ connection established.")
    else:
        logger.error("Failed to establish RabbitMQ connection on startup.")
        # Решить: останавливать приложение или работать без RabbitMQ?
        # Пока просто логируем ошибку.

    yield
    
    # Код после остановки (shutdown)
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    # 1. Закрытие соединения с RabbitMQ
    close_rabbitmq_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Микросервис для управления задачами.",
    version="0.1.0",
    lifespan=lifespan,
    # openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# TODO: Подключить middleware (CORS и др.)

# Подключаем основной роутер API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health Check"])
def read_root():
    return {"message": f"{settings.PROJECT_NAME} is running."} 