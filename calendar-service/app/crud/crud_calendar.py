from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.calendar import Calendar
from app.schemas.calendar import CalendarCreate, CalendarUpdate


class CRUDCalendar(CRUDBase[Calendar, CalendarCreate, CalendarUpdate]):
    async def get_by_owner(self, db: AsyncSession, *, owner_user_id: int) -> List[Calendar]:
        result = await db.execute(
            select(self.model)
            .filter(Calendar.owner_user_id == owner_user_id)
            .filter(Calendar.is_team_calendar == False)
        )
        return result.scalars().all()

    async def get_team_calendars(self, db: AsyncSession, *, team_id: Optional[int] = None, department_id: Optional[int] = None) -> List[Calendar]:
        stmt = select(self.model).filter(Calendar.is_team_calendar == True)
        if team_id:
            stmt = stmt.filter(Calendar.team_id == team_id)
        if department_id:
            stmt = stmt.filter(Calendar.department_id == department_id)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_primary_calendar(self, db: AsyncSession, *, owner_user_id: int) -> Optional[Calendar]:
        result = await db.execute(
            select(self.model)
            .filter(Calendar.owner_user_id == owner_user_id)
            .filter(Calendar.is_primary == True)
            .filter(Calendar.is_team_calendar == False)
        )
        return result.scalars().first()

    # Можно добавить другие специфичные методы, например, поиск по имени и т.д.


calendar = CRUDCalendar(Calendar) 