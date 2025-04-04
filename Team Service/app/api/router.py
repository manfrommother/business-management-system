from fastapi import APIRouter

from app.api import teams, departments, members, news

api_router = APIRouter()

# Включение маршрутов для команд
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])

# Включение маршрутов для отделов
api_router.include_router(departments.router, prefix="", tags=["departments"])

# Включение маршрутов для участников команды
api_router.include_router(members.router, prefix="", tags=["team_members"])

# Включение маршрутов для новостей команды
api_router.include_router(news.router, prefix="", tags=["team_news"])