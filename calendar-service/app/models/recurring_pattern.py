from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Interval, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class FrequencyType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class DayOfWeek(str, enum.Enum): # Для еженедельного повторения
    MONDAY = "mon"
    TUESDAY = "tue"
    WEDNESDAY = "wed"
    THURSDAY = "thu"
    FRIDAY = "fri"
    SATURDAY = "sat"
    SUNDAY = "sun"

class MonthWeek(str, enum.Enum): # Для ежемесячного по номеру недели
    FIRST = "first"
    SECOND = "second"
    THIRD = "third"
    FOURTH = "fourth"
    LAST = "last"


class RecurringPattern(Base):
    id = Column(Integer, primary_key=True, index=True)
    frequency = Column(SQLEnum(FrequencyType), nullable=False)
    interval = Column(Integer, default=1) # Интервал повторения (e.g., каждые 2 недели)
    start_date = Column(Date, nullable=False) # Дата начала действия правила
    end_date = Column(Date, nullable=True) # Дата окончания действия правила
    count = Column(Integer, nullable=True) # Количество повторений

    # Поля для специфичных частот
    days_of_week = Column(JSON, nullable=True) # Список дней недели ["mon", "wed"] для WEEKLY
    day_of_month = Column(Integer, nullable=True) # Число месяца для MONTHLY
    week_of_month = Column(SQLEnum(MonthWeek), nullable=True) # Номер недели в месяце для MONTHLY
    month_of_year = Column(Integer, nullable=True) # Месяц для YEARLY

    # Исключения (даты, когда событие не должно повторяться)
    excluded_dates = Column(JSON, nullable=True, default=list) # Список дат в формате ISO

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи (будут добавлены/дополнены позже)
    # events = relationship("Event", back_populates="recurring_pattern") 