from fastapi import APIRouter
from app.schemas.health import HealthResponse, VersionResponse
from app.core.config import settings

router = APIRouter()

@router.get("", response_model=HealthResponse)
async def health_check():
    """Check the health of the service."""
    return HealthResponse(status="OK")

@router.get("/version", response_model=VersionResponse)
async def get_version():
    """Get the service version."""
    # You might want to read the version from a file or environment variable
    return VersionResponse(version=settings.PROJECT_VERSION) 