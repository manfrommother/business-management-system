import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.core.config import settings
from app.core.messaging import connect_to_rabbitmq, close_rabbitmq_connection

# Setup logging
logging.basicConfig(level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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