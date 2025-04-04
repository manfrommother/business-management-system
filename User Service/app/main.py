import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Импорты для sqladmin
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request as StarletteRequest

from api.router import api_router
from config import settings
from db.session import engine
from db.models import Base, User, VerificationToken
from logging_config import setup_logging
from services.redis import redis_service
from services.messaging import rabbitmq_service
from db.crud import permanently_delete_expired_users
from db.session import SessionLocal

# Добавление представлений для sqladmin
from sqladmin import ModelView

class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.email, User.name, User.is_active, 
        User.is_deleted, User.role, User.created_at
    ]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.id, User.email, User.name, User.created_at]
    column_details_exclude_list = [User.hashed_password]  # Не показываем хеш пароля
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

class VerificationTokenAdmin(ModelView, model=VerificationToken):
    column_list = [VerificationToken.id, VerificationToken.user_id, VerificationToken.type, VerificationToken.expires_at, VerificationToken.is_expired]
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    name = "Токен Верификации"
    name_plural = "Токены Верификации"
    icon = "fa-solid fa-key"

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
    
    # Удаление истекших пользователей
    logger.info("Проверка и удаление истекших пользователей")
    db = SessionLocal()
    try:
        deleted_count = permanently_delete_expired_users(db)
        logger.info(f"Удалено {deleted_count} истекших пользователей")
    finally:
        db.close()
    
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
# Простая аутентификация (ЗАМЕНИТЬ НА БОЛЕЕ БЕЗОПАСНУЮ В ПРОДАШКЕНЕ!)
class BasicAuthBackend(AuthenticationBackend):
    async def login(self, request: StarletteRequest) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        # Здесь должна быть проверка пользователя из БД или конфига
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({"token": "..."})  # Простой токен для примера
            return True
        return False

    async def logout(self, request: StarletteRequest) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: StarletteRequest) -> bool:
        return "token" in request.session

# Добавление переменных для админки в .env.example (и сам .env файл)
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=changeme

# Проверяем, что переменные заданы
if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
    logger.warning(
        "ADMIN_USERNAME и ADMIN_PASSWORD не установлены в настройках. "
        "Используются значения по умолчанию."
    )
    # Устанавливаем значения по умолчанию, если они не заданы
    settings.ADMIN_USERNAME = getattr(settings, 'ADMIN_USERNAME', 'admin')
    settings.ADMIN_PASSWORD = getattr(settings, 'ADMIN_PASSWORD', 'changeme')

authentication_backend = BasicAuthBackend(secret_key=settings.SECRET_KEY) # Используем SECRET_KEY из настроек

admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)
admin.add_view(UserAdmin)
admin.add_view(VerificationTokenAdmin)
# --------------------------

# Настройка CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продe будет заменено на список разрешенных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация маршрутов API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"message": "User Service API", "version": "1.0.0"}

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
    # Включаем поддержку сессий для админки
    app.add_middleware(
        CORSMiddleware,  # Используем существующий middleware, но добавляем сессии
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from starlette.middleware.sessions import SessionMiddleware
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)