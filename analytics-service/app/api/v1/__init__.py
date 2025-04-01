from fastapi import APIRouter

from app.api.v1.endpoints import (
    dashboards, tasks, users, departments, companies, time
)

router = APIRouter()

# Import other endpoint modules here if needed
# Example:
# from . import users, departments, companies, time
# router.include_router(users.router, prefix="/users", tags=["User Analytics"])
# router.include_router(departments.router, prefix="/departments", tags=["Department Analytics"])
# router.include_router(companies.router, prefix="/companies", tags=["Company Analytics"])
# router.include_router(time.router, prefix="/time", tags=["Time Analytics"])

# Include routers for all analytic categories
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks Analytics"])
router.include_router(users.router, prefix="/users", tags=["User Analytics"])
router.include_router(departments.router, prefix="/departments", tags=["Department Analytics"])
router.include_router(companies.router, prefix="/companies", tags=["Company Analytics"])
router.include_router(time.router, prefix="/time", tags=["Time Analytics"])
router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"]) 