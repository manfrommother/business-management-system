from fastapi import FastAPI

# TODO: Импортировать роутеры
from app.api.v1.endpoints import companies, departments, members, invitations, news
# from app.api.v1 import (
#     news
# )

# TODO: Настроить CORS, если необходимо
# from fastapi.middleware.cors import CORSMiddleware

# TODO: Подключить обработчики событий жизненного цикла приложения
# (startup, shutdown)
# from app.db.session import engine, Base
from app.core.config import settings # Импортируем настройки

app = FastAPI(
    title=settings.PROJECT_NAME, # Используем имя из настроек
    description=(
        "Микросервис для управления командами (компаниями), "
        "их структурой, участниками и новостями."
    ),
    version="0.1.0",
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
app.include_router(
    companies.router,
    prefix=f"{settings.API_V1_STR}/companies",
    tags=["Companies"]
)
app.include_router(
    departments.router,
    prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/departments",
    tags=["Departments"]
)
app.include_router(
    members.router,
    prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/members",
    tags=["Members"]
)
app.include_router(
    invitations.router,
    prefix=f"{settings.API_V1_STR}/invitations",
    tags=["Invitations"]
)
app.include_router(
    news.router,
    prefix=f"{settings.API_V1_STR}/companies/{{company_id}}/news",
    tags=["News"]
)
# app.include_router(
#     news.router, prefix="/api/v1/companies/{company_id}/news", tags=["News"]
# )


@app.get("/", tags=["Health Check"])
def read_root():
    return {"message": "Company Administration Service is running."}


# TODO: Реализовать обработчики событий startup/shutdown для
# инициализации БД, подключения к RabbitMQ и т.д.
# @app.on_event("startup")
# async def startup_event():
#     # Пример: Создание таблиц БД (лучше использовать Alembic для миграций)
#     # async with engine.begin() as conn:
#     #     await conn.run_sync(Base.metadata.create_all)
#     pass
#
# @app.on_event("shutdown")
# async def shutdown_event():
#     pass 