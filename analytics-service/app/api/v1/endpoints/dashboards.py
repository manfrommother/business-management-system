from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from app.services import dashboard_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter()

@router.post("/custom", response_model=Dashboard, status_code=status.HTTP_201_CREATED)
async def create_new_dashboard(
    *, 
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    dashboard_in: DashboardCreate
):
    """Creates a new custom dashboard for the authenticated user."""
    if dashboard_in.owner_id != current_user.id:
        dashboard_in.owner_id = current_user.id 

    return await dashboard_service.create_dashboard(db=db, dashboard_in=dashboard_in)

@router.get("/custom/{dashboard_id}", response_model=Dashboard)
async def read_dashboard(
    *,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Gets a specific dashboard by ID. Requires authentication.
       Ensures the dashboard belongs to the authenticated user.
    """
    db_dashboard = await dashboard_service.get_dashboard(db=db, dashboard_id=dashboard_id)
    if db_dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    if db_dashboard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this dashboard")
    return db_dashboard

@router.get("/custom", response_model=List[Dashboard])
async def read_dashboards(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Gets a list of dashboards owned by the authenticated user."""
    dashboards = await dashboard_service.get_dashboards_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return dashboards

@router.put("/custom/{dashboard_id}", response_model=Dashboard)
async def update_existing_dashboard(
    *,
    dashboard_id: int,
    dashboard_in: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Updates a dashboard owned by the authenticated user."""
    db_dashboard = await dashboard_service.get_dashboard(db=db, dashboard_id=dashboard_id)
    if db_dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    if db_dashboard.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this dashboard")
        
    return await dashboard_service.update_dashboard(db=db, db_dashboard=db_dashboard, dashboard_in=dashboard_in)

@router.delete("/custom/{dashboard_id}", response_model=Dashboard)
async def delete_existing_dashboard(
    *,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """Deletes a dashboard owned by the authenticated user."""
    db_dashboard = await dashboard_service.get_dashboard(db=db, dashboard_id=dashboard_id)
    if db_dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found")
    if db_dashboard.owner_id != current_user.id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this dashboard")

    deleted_dashboard = await dashboard_service.delete_dashboard(db=db, dashboard_id=dashboard_id)
    if deleted_dashboard is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found after delete attempt")
    return deleted_dashboard

@router.get("/overview", response_model=dict)
async def get_dashboard_overview(
    *, 
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """(Placeholder) Gets general overview data for dashboards."""
    return {"message": "Overview endpoint not implemented yet"}

@router.get("/performance", response_model=dict)
async def get_dashboard_performance(
    *, 
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """(Placeholder) Gets performance data for dashboards."""
    return {"message": "Performance endpoint not implemented yet"}

@router.get("/workload", response_model=dict)
async def get_dashboard_workload(
    *, 
    db: AsyncSession = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """(Placeholder) Gets workload data for dashboards."""
    return {"message": "Workload endpoint not implemented yet"} 