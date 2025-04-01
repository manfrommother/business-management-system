import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.core.config import settings
from app.core.messaging import connect_to_rabbitmq, close_rabbitmq_connection
from app.db.session import engine

# Импорты для sqladmin
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request as StarletteRequest
from starlette.middleware.sessions import SessionMiddleware
from app.admin import (
    AnalyticsDataAdmin, MetricAdmin, ReportAdmin, DashboardAdmin
)

# Setup logging
logging.basicConfig(level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
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
admin.add_view(AnalyticsDataAdmin)
admin.add_view(MetricAdmin)
admin.add_view(ReportAdmin)
admin.add_view(DashboardAdmin)
# --------------------------

# Добавляем SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS: # Assuming BACKEND_CORS_ORIGINS is added to Settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Allow all origins if not specified (useful for development)
    logger.warning("CORS origins not specified, allowing all origins.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Analytics Service...")
    await connect_to_rabbitmq()
    # Add other startup logic here (e.g., connect to DB, Redis)
    # await connect_to_db()
    # await connect_to_redis()
    # Start consumers? Maybe better handled by Celery workers or separate processes.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Analytics Service...")
    await close_rabbitmq_connection()
    # Add other shutdown logic here (e.g., disconnect from DB, Redis)
    # await disconnect_from_db()
    # await disconnect_from_redis()

# Добавим порт по умолчанию 8003
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True) 