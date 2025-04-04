from pydantic import BaseModel
from typing import Optional
import datetime

from .base import BaseSchema, BaseSchemaWithId
from app.models.event_attendee import AttendeeStatus


class EventAttendeeBase(BaseSchema):
    user_id: int
    status: AttendeeStatus = AttendeeStatus.NEEDS_ACTION
    response_comment: Optional[str] = None


class EventAttendeeCreate(EventAttendeeBase):
    event_id: int
    # user_id берется из Base
    pass


class EventAttendeeUpdate(BaseSchema):
    status: Optional[AttendeeStatus] = None
    response_comment: Optional[str] = None


class EventAttendeeStatusUpdate(BaseSchema): # Отдельная схема для PUT /status
    status: AttendeeStatus


class EventAttendeeInDBBase(BaseSchemaWithId, EventAttendeeBase):
    event_id: int
    added_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class EventAttendee(EventAttendeeInDBBase):
    # Можно добавить информацию о пользователе, если нужно
    # user: Optional[UserSchema] = None # Зависит от User Service
    pass 