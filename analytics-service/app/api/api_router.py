from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1 import router as v1_router

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(v1_router, prefix="/v1/analytics") 