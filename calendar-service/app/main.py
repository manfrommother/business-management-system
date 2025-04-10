from fastapi import FastAPI
import logging

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine  # Импортируем engine
from app.db.base import Base  # Импортируем Base

# Импорты для sqladmin
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request as StarletteRequest
from starlette.middleware.sessions import SessionMiddleware
from app.admin import (
    EventAdmin, CalendarAdmin, EventAttendeeAdmin,
    EventReminderAdmin, RecurringPatternAdmin, UserSettingAdmin
)

logger = logging.getLogger(__name__)

# --- Создание таблиц при старте (для разработки/MVP) ---
async def create_db_and_tables():
    async with engine.begin() as conn:
        logger.info("Dropping all tables...")  # Опционально: очистка перед созданием
        # await conn.run_sync(Base.metadata.drop_all)
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created.")

# -----------------------------------------------------

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

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

# Проверяем переменные админа и SECRET_KEY
if not hasattr(settings, 'ADMIN_USERNAME') or not hasattr(settings, 'ADMIN_PASSWORD'):
    logger.warning(
        "ADMIN_USERNAME/ADMIN_PASSWORD не установлены. "
        "Используются значения по умолчанию."
    )
    settings.ADMIN_USERNAME = getattr(settings, 'ADMIN_USERNAME', 'admin')
    settings.ADMIN_PASSWORD = getattr(settings, 'ADMIN_PASSWORD', 'changeme')

if not hasattr(settings, 'SECRET_KEY') or not settings.SECRET_KEY:
    logger.error("SECRET_KEY не установлен! Админка не будет работать.")
    raise ValueError("SECRET_KEY не установлен в настройках!")

authentication_backend = BasicAuthBackend(secret_key=settings.SECRET_KEY)
admin = Admin(app=app, engine=engine, authentication_backend=authentication_backend)

# Добавляем представления моделей в админку
admin.add_view(EventAdmin)
admin.add_view(CalendarAdmin)
admin.add_view(EventAttendeeAdmin)
admin.add_view(EventReminderAdmin)
admin.add_view(RecurringPatternAdmin)
admin.add_view(UserSettingAdmin)
# --------------------------

# Добавляем SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

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

# Добавим порт по умолчанию 8002
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True) 