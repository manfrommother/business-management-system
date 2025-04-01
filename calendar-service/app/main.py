from fastapi import FastAPI
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine # Импортируем engine
from app.db.base import Base # Импортируем Base (не Base из base_class!)

logger = logging.getLogger(__name__)

# --- Создание таблиц при старте (для разработки/MVP) ---
async def create_db_and_tables():
    async with engine.begin() as conn:
        logger.info("Dropping all tables...") # Опционально: очистка перед созданием
        # await conn.run_sync(Base.metadata.drop_all)
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created.")

# -----------------------------------------------------

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

@app.on_event("startup")
async def on_startup():
    logger.info("Starting up...")
    await create_db_and_tables() # Вызываем создание таблиц
    # Здесь же можно инициализировать подключения к RabbitMQ, Redis и т.д.

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down...")
    # Закрыть соединения, если нужно


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

# Подключаем маршрутизатор API v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Здесь можно добавить обработчики событий startup/shutdown,
# например, для подключения к RabbitMQ или Redis 