from .base import CRUDBase
from .crud_calendar import calendar
from .crud_event import event
from .crud_event_attendee import event_attendee
# from .crud_event_reminder import event_reminder # Добавить, если будет создан CRUD
from .crud_user_setting import user_setting

# Добавляем CRUD для RecurringPattern, используя базовый класс
from app.models.recurring_pattern import RecurringPattern
from app.schemas.recurring_pattern import RecurringPatternCreate, RecurringPatternUpdate
recurring_pattern = CRUDBase[RecurringPattern, RecurringPatternCreate, RecurringPatternUpdate](RecurringPattern)

# Можно добавить CRUD классы для EventReminder, если потребуется сложная логика.
# Если нет, можно использовать базовый CRUDBase напрямую:
# from app.models.event_reminder import EventReminder
# from app.schemas.event_reminder import EventReminderCreate, EventReminderUpdate
# event_reminder = CRUDBase[EventReminder, EventReminderCreate, EventReminderUpdate](EventReminder) 