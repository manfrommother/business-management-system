# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.calendar import Calendar  # noqa
from app.models.event import Event  # noqa
from app.models.event_attendee import EventAttendee # noqa
from app.models.event_reminder import EventReminder # noqa
from app.models.recurring_pattern import RecurringPattern # noqa
from app.models.user_setting import UserSetting # noqa
# ... импортировать другие модели здесь
# Например:
# from app.models.event_attendee import EventAttendee # noqa
# from app.models.recurring_pattern import RecurringPattern # noqa
# from app.models.user_setting import UserSetting # noqa 