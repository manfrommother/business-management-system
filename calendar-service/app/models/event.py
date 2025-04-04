from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, DateTime, Text,
    Enum as SQLEnum
)
from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship # Закомментировано, пока не используется
import enum

from app.db.base_class import Base


# Перечисления для типов и статусов событий, видимости
class EventType(str, enum.Enum):
    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    PERSONAL = "personal"
    TIME_BLOCK = "time_block"


class EventVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PARTICIPANTS_ONLY = "participants_only"


class EventStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class Event(Base):
    id = Column(Integer, primary_key=True, index=True)
    calendar_id = Column(
        Integer, ForeignKey("calendars.id"), nullable=False, index=True
    )
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    event_type = Column(
        SQLEnum(EventType), nullable=False, default=EventType.MEETING
    )
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    creator_user_id = Column(Integer, index=True, nullable=False)
    is_all_day = Column(Boolean, default=False)
    visibility = Column(
        SQLEnum(EventVisibility),
        nullable=False,
        default=EventVisibility.PARTICIPANTS_ONLY
    )
    recurring_pattern_id = Column(
        Integer, ForeignKey("recurring_patterns.id"), nullable=True, index=True
    )
    task_id = Column(Integer, index=True, nullable=True)  # ID связанной задачи
    status = Column(
        SQLEnum(EventStatus), nullable=False, default=EventStatus.CONFIRMED
    )
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи (будут добавлены позже)
    # calendar = relationship("Calendar", back_populates="events")
    # attendees = relationship("EventAttendee", back_populates="event")
    # reminders = relationship("EventReminder", back_populates="event")
    # recurring_pattern = relationship(
    #     "RecurringPattern", back_populates="events"
    # ) 