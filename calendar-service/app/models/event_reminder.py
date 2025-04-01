from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Interval, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class EventReminder(Base):
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True) # Для кого напоминание
    # Время напоминания может быть абсолютным или относительным
    reminder_time_before = Column(Interval, nullable=True) # За сколько до события напомнить (e.g., '15 minutes')
    reminder_absolute_time = Column(DateTime(timezone=True), nullable=True) # Конкретное время напоминания
    notification_method = Column(String, nullable=False, default="app") # Метод: app, email
    is_sent = Column(Boolean, default=False, index=True) # Отправлено ли напоминание
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи (будут добавлены/дополнены позже)
    # event = relationship("Event", back_populates="reminders") 