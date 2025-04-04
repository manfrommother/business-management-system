from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update

from app.crud.base import CRUDBase
from app.models.event_attendee import EventAttendee, AttendeeStatus
from app.schemas.event_attendee import EventAttendeeCreate, EventAttendeeUpdate


class CRUDEventAttendee(CRUDBase[EventAttendee, EventAttendeeCreate, EventAttendeeUpdate]):

    async def get_multi_by_event(self, db: AsyncSession, *, event_id: int) -> List[EventAttendee]:
        result = await db.execute(
            select(self.model).filter(EventAttendee.event_id == event_id)
        )
        return result.scalars().all()

    async def get_by_event_and_user(self, db: AsyncSession, *, event_id: int, user_id: int) -> Optional[EventAttendee]:
        result = await db.execute(
            select(self.model)
            .filter(EventAttendee.event_id == event_id)
            .filter(EventAttendee.user_id == user_id)
        )
        return result.scalars().first()

    async def update_status(self, db: AsyncSession, *, event_id: int, user_id: int, status: AttendeeStatus) -> Optional[EventAttendee]:
        attendee = await self.get_by_event_and_user(db=db, event_id=event_id, user_id=user_id)
        if not attendee:
            return None
        attendee.status = status
        db.add(attendee)
        await db.commit()
        await db.refresh(attendee)
        return attendee

    async def remove_by_event_and_user(self, db: AsyncSession, *, event_id: int, user_id: int) -> Optional[EventAttendee]:
        attendee = await self.get_by_event_and_user(db=db, event_id=event_id, user_id=user_id)
        if attendee:
            await db.delete(attendee)
            await db.commit()
        return attendee

    async def add_attendees_to_event(self, db: AsyncSession, *, event_id: int, user_ids: List[int]) -> List[EventAttendee]:
        attendees = []
        for user_id in user_ids:
            # Проверяем, нет ли уже такого участника
            existing = await self.get_by_event_and_user(db=db, event_id=event_id, user_id=user_id)
            if not existing:
                attendee_in = EventAttendeeCreate(event_id=event_id, user_id=user_id)
                attendee = await self.create(db=db, obj_in=attendee_in)
                attendees.append(attendee)
        return attendees


event_attendee = CRUDEventAttendee(EventAttendee) 