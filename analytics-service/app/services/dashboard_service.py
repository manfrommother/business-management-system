from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.db.models.dashboard import Dashboard
from app.schemas.dashboard import DashboardCreate, DashboardUpdate


async def create_dashboard(db: AsyncSession, dashboard_in: DashboardCreate) -> Dashboard:
    """Creates a new dashboard in the database."""
    db_dashboard = Dashboard(**dashboard_in.model_dump())
    db.add(db_dashboard)
    await db.commit()
    await db.refresh(db_dashboard)
    return db_dashboard

async def get_dashboard(db: AsyncSession, dashboard_id: int) -> Optional[Dashboard]:
    """Gets a specific dashboard by its ID."""
    result = await db.execute(select(Dashboard).filter(Dashboard.id == dashboard_id))
    return result.scalars().first()

async def get_dashboards_by_owner(db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100) -> List[Dashboard]:
    """Gets a list of dashboards for a specific owner."""
    result = await db.execute(
        select(Dashboard)
        .filter(Dashboard.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_dashboard(db: AsyncSession, db_dashboard: Dashboard, dashboard_in: DashboardUpdate) -> Dashboard:
    """Updates an existing dashboard."""
    update_data = dashboard_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dashboard, key, value)
    await db.commit()
    await db.refresh(db_dashboard)
    return db_dashboard

async def delete_dashboard(db: AsyncSession, dashboard_id: int) -> Optional[Dashboard]:
    """Deletes a dashboard by its ID."""
    db_dashboard = await get_dashboard(db, dashboard_id)
    if db_dashboard:
        await db.delete(db_dashboard)
        await db.commit()
    return db_dashboard 