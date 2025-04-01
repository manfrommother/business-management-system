# flake8: noqa
from sqladmin import ModelView
from app.models import (
    Event, EventAttendee, EventReminder, RecurringPattern, Calendar, UserSetting
)


class EventAdmin(ModelView, model=Event):
    column_list = [Event.id, Event.title, Event.calendar_id, Event.start_time, Event.end_time, Event.is_recurring, Event.created_by]
    column_searchable_list = [Event.title, Event.description]
    column_sortable_list = [Event.start_time, Event.end_time, Event.created_at]
    name = "Событие"
    name_plural = "События"
    icon = "fa-solid fa-calendar-day"


class CalendarAdmin(ModelView, model=Calendar):
    column_list = [Calendar.id, Calendar.name, Calendar.user_id, Calendar.is_primary, Calendar.created_at]
    column_searchable_list = [Calendar.name]
    column_sortable_list = [Calendar.name, Calendar.created_at]
    name = "Календарь"
    name_plural = "Календари"
    icon = "fa-solid fa-calendar"


class EventAttendeeAdmin(ModelView, model=EventAttendee):
    column_list = [EventAttendee.id, EventAttendee.event_id, EventAttendee.user_id, EventAttendee.status]
    column_searchable_list = [EventAttendee.user_id]
    column_sortable_list = [EventAttendee.event_id, EventAttendee.user_id]
    name = "Участник События"
    name_plural = "Участники Событий"
    icon = "fa-solid fa-user-check"


class EventReminderAdmin(ModelView, model=EventReminder):
    column_list = [EventReminder.id, EventReminder.event_id, EventReminder.remind_at, EventReminder.method]
    column_searchable_list = [EventReminder.event_id]
    column_sortable_list = [EventReminder.remind_at]
    name = "Напоминание"
    name_plural = "Напоминания"
    icon = "fa-solid fa-bell"


class RecurringPatternAdmin(ModelView, model=RecurringPattern):
    column_list = [RecurringPattern.id, RecurringPattern.event_id, RecurringPattern.frequency, RecurringPattern.end_date]
    column_searchable_list = [RecurringPattern.event_id]
    column_sortable_list = [RecurringPattern.event_id, RecurringPattern.end_date]
    name = "Шаблон Повторения"
    name_plural = "Шаблоны Повторения"
    icon = "fa-solid fa-repeat"


class UserSettingAdmin(ModelView, model=UserSetting):
    column_list = [UserSetting.id, UserSetting.user_id, UserSetting.timezone, UserSetting.default_calendar_id]
    column_searchable_list = [UserSetting.user_id]
    column_sortable_list = [UserSetting.user_id]
    name = "Настройки Пользователя"
    name_plural = "Настройки Пользователей"
    icon = "fa-solid fa-cog" 