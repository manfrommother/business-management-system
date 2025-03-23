from fastapi import APIRouter

from app.api import auth, profile

api_router = APIRouter()

# Включение маршрутов аутентификации
api_router.include_router(auth.router, tags=["authentication"])

# Включение маршрутов профиля
api_router.include_router(profile.router, tags=["profile"])