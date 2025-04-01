from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

from .base import BaseSchema, BaseSchemaWithId
from .recurring_pattern import RecurringPatternCreate, RecurringPattern # Добавляем RecurringPattern
from app.models.event import EventType, EventVisibility, EventStatus # Импортируем Enum

# Общие поля
class EventBase(BaseSchema):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: EventType = EventType.MEETING
    start_time: datetime.datetime
    end_time: datetime.datetime
    is_all_day: bool = False
    visibility: EventVisibility = EventVisibility.PARTICIPANTS_ONLY
    task_id: Optional[int] = None

# Поля для создания
class EventCreate(EventBase):
    calendar_id: int
    creator_user_id: int # Должен быть установлен при создании
    attendee_user_ids: List[int] = [] # Список ID участников для добавления
    recurring_pattern: Optional[RecurringPatternCreate] = None # Поле для передачи правила повторения
    # Статус при создании обычно CONFIRMED

# Поля для обновления (все опциональные)
class EventUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[EventType] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    is_all_day: Optional[bool] = None
    visibility: Optional[EventVisibility] = None
    status: Optional[EventStatus] = None # Можно изменить статус (e.g., отменить)
    recurring_pattern_id: Optional[int] = None
    task_id: Optional[int] = None
    # calendar_id обычно не меняется
    # creator_user_id не меняется


# Схема для данных в БД
class EventInDBBase(BaseSchemaWithId, EventBase):
    calendar_id: int
    creator_user_id: int
    recurring_pattern_id: Optional[int]
    status: EventStatus
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


# Схема для возврата через API
class Event(EventInDBBase):
    # Добавляем вложенную схему для правила повторения
    recurring_pattern: Optional[RecurringPattern] = None

    # Здесь можно добавить связанные данные, если нужно
    # attendees: List[EventAttendee] = []
    # reminders: List[EventReminder] = []

    class Config:
        from_attributes = True # Убедимся, что ORM режим включен (для Pydantic V2)

# Схема для восстановления удаленного события
class EventRestore(BaseModel):
    event_id: int 