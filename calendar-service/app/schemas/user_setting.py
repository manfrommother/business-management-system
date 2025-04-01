from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import datetime

from .base import BaseSchema

# Т.к. PK это user_id, отдельная схема с ID не нужна
class UserSettingBase(BaseSchema):
    timezone: str = "UTC"
    default_event_duration: int = Field(default=60, gt=0) # В минутах
    week_start_day: str = "mon"
    working_hours_start: Optional[datetime.time] = None
    working_hours_end: Optional[datetime.time] = None
    working_days: List[str] = Field(default=["mon", "tue", "wed", "thu", "fri"])
    show_weekends: bool = True
    default_view: str = "week"
    notification_preferences: Dict[str, Any] = Field(default={})

    # Можно добавить валидаторы для working_days, timezone и т.д.


class UserSettingCreate(UserSettingBase):
    user_id: int
    pass # Пока совпадает с Base + user_id


class UserSettingUpdate(BaseSchema):
    timezone: Optional[str] = None
    default_event_duration: Optional[int] = Field(default=None, gt=0)
    week_start_day: Optional[str] = None
    working_hours_start: Optional[datetime.time] = None
    working_hours_end: Optional[datetime.time] = None
    working_days: Optional[List[str]] = None
    show_weekends: Optional[bool] = None
    default_view: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None


class UserSettingInDBBase(UserSettingBase):
    user_id: int
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class UserSetting(UserSettingInDBBase):
    pass 