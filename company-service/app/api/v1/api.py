# company-service/app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import companies, departments, members, invitations, news

api_router = APIRouter()

# Маршруты, связанные непосредственно с компаниями (создание, список, получение, обновление, удаление, статистика)
# и создание приглашений для конкретной компании
api_router.include_router(companies.router, prefix="/companies", tags=["Companies & Invitations (Company Scope)"])

# Маршруты для отделов внутри компании
api_router.include_router(
    departments.router,
    prefix="/companies/{company_id}/departments",
    tags=["Departments"],
)

# Маршруты для управления членством пользователей в компании
api_router.include_router(
    members.router,
    prefix="/companies/{company_id}/members",
    tags=["Memberships"],
)

# Маршруты для проверки и принятия приглашений (не привязаны к ID компании в URL)
api_router.include_router(invitations.router, prefix="/invitations", tags=["Invitations (General)"])

# Маршруты для новостей внутри компании
api_router.include_router(
    news.router,
    prefix="/companies/{company_id}/news",
    tags=["News"],
) 