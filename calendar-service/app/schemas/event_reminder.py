from pydantic import BaseModel, validator
from typing import Optional
import datetime

from .base import BaseSchema, BaseSchemaWithId


class EventReminderBase(BaseSchema):
    user_id: int
    reminder_time_before: Optional[datetime.timedelta] = None
    reminder_absolute_time: Optional[datetime.datetime] = None
    notification_method: str = "app"

    @validator('reminder_absolute_time', 'reminder_time_before', pre=True, always=True)
    def check_reminder_time_set(cls, v, values):
        if values.get('reminder_time_before') is None and values.get('reminder_absolute_time') is None:
            raise ValueError('Either reminder_time_before or reminder_absolute_time must be set')
        if values.get('reminder_time_before') is not None and values.get('reminder_absolute_time') is not None:
            raise ValueError('Only one of reminder_time_before or reminder_absolute_time can be set')
        return v


class EventReminderCreate(EventReminderBase):
    event_id: int
    pass


class EventReminderUpdate(BaseSchema):
    reminder_time_before: Optional[datetime.timedelta] = None
    reminder_absolute_time: Optional[datetime.datetime] = None
    notification_method: Optional[str] = None
    is_sent: Optional[bool] = None # Можно вручную пометить как отправленное?

    # Валидатор нужно будет скопировать или вынести, если он нужен и здесь


class EventReminderInDBBase(BaseSchemaWithId, EventReminderBase):
    event_id: int
    is_sent: bool
    created_at: datetime.datetime


class EventReminder(EventReminderInDBBase):
    pass 