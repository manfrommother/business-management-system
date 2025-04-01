from pydantic import BaseModel, validator, Field
from typing import Optional, List
import datetime

from .base import BaseSchema, BaseSchemaWithId
from app.models.recurring_pattern import FrequencyType, DayOfWeek, MonthWeek


class RecurringPatternBase(BaseSchema):
    frequency: FrequencyType
    interval: int = Field(default=1, gt=0)
    start_date: datetime.date
    end_date: Optional[datetime.date] = None
    count: Optional[int] = Field(default=None, gt=0)

    # Поля для специфичных частот
    days_of_week: Optional[List[DayOfWeek]] = None # Для WEEKLY
    day_of_month: Optional[int] = Field(default=None, ge=1, le=31) # Для MONTHLY
    week_of_month: Optional[MonthWeek] = None # Для MONTHLY
    month_of_year: Optional[int] = Field(default=None, ge=1, le=12) # Для YEARLY

    excluded_dates: List[datetime.date] = []

    # Добавить валидаторы для проверки консистентности полей в зависимости от frequency
    @validator('days_of_week', pre=True, always=True)
    def check_days_of_week(cls, v, values):
        if values.get('frequency') == FrequencyType.WEEKLY and not v:
            raise ValueError("days_of_week must be provided for weekly frequency")
        if values.get('frequency') != FrequencyType.WEEKLY and v:
            raise ValueError("days_of_week can only be set for weekly frequency")
        return v

    # ... Подобные валидаторы для day_of_month, week_of_month, month_of_year
    # ... Валидатор для end_date/count (должно быть что-то одно)


class RecurringPatternCreate(RecurringPatternBase):
    pass


class RecurringPatternUpdate(BaseSchema):
    # Позволить обновлять только некоторые поля, например, end_date или excluded_dates
    end_date: Optional[datetime.date] = None
    count: Optional[int] = Field(default=None, gt=0)
    excluded_dates: Optional[List[datetime.date]] = None
    # Возможно, стоит запретить изменять frequency, interval и т.д. после создания


class RecurringPatternInDBBase(BaseSchemaWithId, RecurringPatternBase):
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class RecurringPattern(RecurringPatternInDBBase):
    pass 