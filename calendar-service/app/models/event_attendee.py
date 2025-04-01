from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class AttendeeStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    NEEDS_ACTION = "needs_action" # По умолчанию при добавлении


class EventAttendee(Base):
    # Комбинированный первичный ключ не нужен, если есть свой id
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True) # ID пользователя из User Service
    status = Column(SQLEnum(AttendeeStatus), nullable=False, default=AttendeeStatus.NEEDS_ACTION)
    response_comment = Column(String, nullable=True) # Комментарий при ответе
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Уникальность пары event_id и user_id
    __table_args__ = (UniqueConstraint('event_id', 'user_id', name='_event_user_uc'),)

    # Связи (будут добавлены/дополнены позже)
    # event = relationship("Event", back_populates="attendees") 