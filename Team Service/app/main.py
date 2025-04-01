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

# Импорты для sqladmin
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request as StarletteRequest
from starlette.middleware.sessions import SessionMiddleware

# Импортируем представления из admin.py
from app.admin import (
    TeamAdmin, DepartmentAdmin, TeamMemberAdmin, 
    TeamInviteAdmin, TeamNewsAdmin
)

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

# --- Интеграция SQLAdmin --- 
# Используем тот же BasicAuthBackend (ЗАМЕНИТЬ НА БОЛЕЕ БЕЗОПАСНУЮ В ПРОДАКШЕНЕ!)
class BasicAuthBackend(AuthenticationBackend):
    async def login(self, request: StarletteRequest) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": "authenticated"}) 
            return True
        return False

    async def logout(self, request: StarletteRequest) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: StarletteRequest) -> bool:
        return "token" in request.session

# Проверяем, что переменные админа заданы в настройках
if not hasattr(settings, 'ADMIN_USERNAME') or not hasattr(settings, 'ADMIN_PASSWORD'):
    logger.warning(
        "ADMIN_USERNAME и ADMIN_PASSWORD не установлены в настройках. "
        "Используются значения по умолчанию."
    )
    settings.ADMIN_USERNAME = getattr(settings, 'ADMIN_USERNAME', 'admin')
    settings.ADMIN_PASSWORD = getattr(settings, 'ADMIN_PASSWORD', 'changeme')

# Проверяем наличие SECRET_KEY
if not hasattr(settings, 'SECRET_KEY') or not settings.SECRET_KEY:
    logger.error(
        "SECRET_KEY не установлен в настройках! "
        "Админка не будет работать без секретного ключа."
    )
    # В реальном приложении здесь можно было бы генерировать временный ключ 
    # или прерывать запуск, но для примера продолжим с предупреждением.
    # Для работы сессий ключ обязателен!
    # settings.SECRET_KEY = "a_default_but_unsafe_secret_key"
    # exit(1) # Лучше прервать запуск
    raise ValueError("SECRET_KEY не установлен в настройках!")

authentication_backend = BasicAuthBackend(secret_key=settings.SECRET_KEY)
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

# Добавляем представления моделей в админку
admin.add_view(TeamAdmin)
admin.add_view(DepartmentAdmin)
admin.add_view(TeamMemberAdmin)
admin.add_view(TeamInviteAdmin)
admin.add_view(TeamNewsAdmin)
# ---------------------------------------------

# Добавляем SessionMiddleware ДО CORSMiddleware или других middleware, работающих с request
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

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
    # Запускаем на порту 8001
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)