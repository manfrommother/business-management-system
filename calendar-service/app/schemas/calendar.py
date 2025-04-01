from pydantic import BaseModel
from typing import Optional
import datetime

from .base import BaseSchema, BaseSchemaWithId


# Общие поля, которые есть и при создании, и при чтении
class CalendarBase(BaseSchema):
    name: str
    description: Optional[str] = None
    is_team_calendar: bool = False
    team_id: Optional[int] = None
    department_id: Optional[int] = None


# Поля, необходимые при создании календаря
class CalendarCreate(CalendarBase):
    owner_user_id: Optional[int] = None # Может быть None для командных
    pass # Пока совпадает с Base, но может отличаться


# Поля, которые можно обновлять (все опциональные)
class CalendarUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_primary: Optional[bool] = None
    # team_id/department_id/owner_id обычно не меняются при обновлении


# Схема для данных, хранящихся в БД (включает ID и служебные поля)
class CalendarInDBBase(BaseSchemaWithId, CalendarBase):
    owner_user_id: Optional[int]
    is_primary: bool
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


# Схема для возврата данных через API
class Calendar(CalendarInDBBase):
    pass 