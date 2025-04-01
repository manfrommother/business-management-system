from typing import List, Optional, Any
import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.event import Event
from app.models.recurring_pattern import RecurringPattern
from app.schemas.event import EventCreate, EventUpdate


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[Event]:
        """Получает событие по ID с предзагрузкой recurring_pattern."""
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.recurring_pattern))
            .filter(self.model.id == id)
        )
        return result.scalars().first()

    async def get_multi_by_calendar(
        self, db: AsyncSession, *, calendar_id: int, skip: int = 0, limit: int = 100
    ) -> List[Event]:
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.recurring_pattern))
            .filter(Event.calendar_id == calendar_id)
            .filter(Event.is_deleted == False)
            .offset(skip)
            .limit(limit)
            .order_by(Event.start_time) # Сортируем по времени начала
        )
        return result.scalars().all()

    async def get_multi_by_calendar_and_time_range(
        self,
        db: AsyncSession,
        *,
        calendar_id: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Event]:
        result = await db.execute(
            select(self.model)
            .filter(Event.calendar_id == calendar_id)
            .filter(Event.is_deleted == False)
            .filter(
                and_(
                    Event.start_time < end_time, # Событие начинается до конца интервала
                    Event.end_time > start_time   # Событие заканчивается после начала интервала
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Event.start_time)
        )
        return result.scalars().all()

    # Метод для создания события с участниками (потребует CRUDEventAttendee)
    # async def create_with_attendees(...)

    # Метод для мягкого удаления (используем из CRUDBase)
    async def delete_event(self, db: AsyncSession, *, event_id: int) -> Optional[Event]:
        return await self.mark_as_deleted(db=db, id=event_id)

    # Метод для восстановления (используем из CRUDBase)
    async def restore_event(self, db: AsyncSession, *, event_id: int) -> Optional[Event]:
        return await self.restore(db=db, id=event_id)

    # Можно добавить методы для фильтрации по типу, статусу, участнику и т.д.


event = CRUDEvent(Event) 