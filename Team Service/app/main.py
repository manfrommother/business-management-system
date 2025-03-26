import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from app.api.router import api_router
from app.config import settings
from app.db.session import engine
from app.db.models import Base
from app.logging_config import setup_logging
from app.services.redis import redis_service
from app.services.messaging import rabbitmq_service

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Действия при запуске и остановке приложения"""
    # Инициализация сервисов при запуске
    logger.info("Инициализация приложения")
    
    # Создание таблиц в БД, если они не существуют
    logger.info("Создание таблиц базы данных")
    Base.metadata.create_all(bind=engine)
    
    # Подключение к Redis
    logger.info("Подключение к Redis")
    await redis_service.connect()
    
    # Подключение к RabbitMQ
    logger.info("Подключение к RabbitMQ")
    await rabbitmq_service.connect()
    
    logger.info("Приложение успешно инициализировано")
    yield
    
    # Закрытие соединений при остановке
    logger.info("Остановка приложения")
    await redis_service.close()
    await rabbitmq_service.close()
    logger.info("Соединения закрыты")


# Создание экземпляра FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Настройка CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде будет заменено на список разрешенных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация маршрутов API
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"message": "Team Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy"}


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанное исключение: {str(exc)}", exc_info=True, extra={
        "path": request.url.path,
        "method": request.method,
        "client_host": request.client.host if request.client else None
    })
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"}
    )


if __name__ == "__main__":
    """Запуск приложения для локальной разработки"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)