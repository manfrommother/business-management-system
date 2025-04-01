import logging # Добавляем логгер
from contextlib import asynccontextmanager

from fastapi import FastAPI

# TODO: Импортировать роутеры
# Убираем импорты отдельных роутеров
# from app.api.v1.endpoints import companies, departments, members, invitations, news
# Импортируем агрегированный роутер
from app.api.v1.api import api_router
# from app.api.v1 import (
#     news
# )

# TODO: Настроить CORS, если необходимо
# from fastapi.middleware.cors import CORSMiddleware

# TODO: Подключить обработчики событий жизненного цикла приложения
# (startup, shutdown)
# from app.db.session import engine, Base
from app.core.config import settings # Импортируем настройки
from app.db.session import engine # Импортируем engine
from app.db.base import Base  # Импортируем Base для метаданных

logger = logging.getLogger(__name__) # Инициализируем логгер

# Используем новый стиль lifespan для FastAPI >= 0.90
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код перед запуском (startup)
    logger.info(f"Starting up {settings.PROJECT_NAME}...")

    # Создаем таблицы в БД (подходит для разработки, НЕ для продакшена!)
    # В продакшене используйте Alembic для миграций.
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # В зависимости от критичности, можно либо продолжить, либо остановить приложение

    # Сюда можно добавить инициализацию RabbitMQ, Redis и т.д.
    yield
    # Код после остановки (shutdown)
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    # Сюда можно добавить закрытие соединений
    # Например:
    # await disconnect_from_db()
    # await disconnect_from_rabbitmq()

app = FastAPI(
    title=settings.PROJECT_NAME, # Используем имя из настроек
    description=(
        "Микросервис для управления командами (компаниями), "
        "их структурой, участниками и новостями."
    ),
    version="0.1.0",
    lifespan=lifespan # Подключаем lifespan
    # TODO: Добавить другие параметры OpenAPI, если нужно
    # openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# TODO: Подключить middleware (например, CORS)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.BACKEND_CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# TODO: Подключить роутеры
# Убираем подключение отдельных роутеров
# app.include_router(
#     companies.router,
#     prefix=f"{settings.API_V1_STR}/companies",
#     tags=["Companies"]
# )
# app.include_router(
#     departments.router,
#     prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/departments",
#     tags=["Departments"]
# )
# app.include_router(
#     members.router,
#     prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/members",
#     tags=["Members"]
# )
# app.include_router(
#     invitations.router,
#     prefix=f"{settings.API_V1_STR}/invitations",
#     tags=["Invitations"]
# )
# app.include_router(
#     news.router,
#     prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/news",
#     tags=["News"]
# )

# Подключаем единый роутер для API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health Check"])
def read_root():
    return {"message": "Company Administration Service is running."}


# Убираем старые TODO и закомментированные обработчики on_event
# TODO: Реализовать обработчики событий startup/shutdown для
# инициализации БД, подключения к RabbitMQ и т.д.
# @app.on_event("startup")
# async def startup_event():
#     # Пример: Создание таблиц БД (лучше использовать Alembic для миграций)
#     # async with engine.begin() as conn:
#     #     await conn.run_sync(Base.metadata.create_all)
#     logger.info("Application startup complete.")
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("Application shutdown complete.")
#     pass 