from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Time, JSON, DateTime
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserSetting(Base):
    # Используем user_id как первичный ключ, т.к. у каждого пользователя один набор настроек
    user_id = Column(Integer, primary_key=True, index=True) # ID пользователя из User Service
    timezone = Column(String, default="UTC") # Часовой пояс пользователя
    default_event_duration = Column(Integer, default=60) # Длительность события по умолчанию в минутах
    week_start_day = Column(String, default="mon") # Первый день недели (mon, sun, etc.)
    working_hours_start = Column(Time, nullable=True) # Начало рабочего дня
    working_hours_end = Column(Time, nullable=True) # Конец рабочего дня
    working_days = Column(JSON, nullable=True, default=["mon", "tue", "wed", "thu", "fri"]) # Рабочие дни недели
    show_weekends = Column(Boolean, default=True) # Показывать ли выходные в календаре
    default_view = Column(String, default="week") # Вид календаря по умолчанию (day, week, month)
    notification_preferences = Column(JSON, nullable=True) # Настройки уведомлений (e.g., {"email": true, "app": true})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с пользователем (если User модель будет здесь или через ID)
 