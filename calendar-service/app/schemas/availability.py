from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

# Схема для запроса проверки доступности
class AvailabilityQuery(BaseModel):
    user_ids: List[int] = Field(..., min_length=1)
    start_time: datetime.datetime
    end_time: datetime.datetime
    # Опционально: учитывать только рабочее время?
    # only_working_hours: bool = False

# Схема для представления занятого слота времени
class BusySlot(BaseModel):
    user_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    event_id: Optional[int] = None # ID события, вызвавшего занятость (опционально)
    event_title: Optional[str] = None # Название события (опционально)

# Схема ответа для проверки доступности
class AvailabilityResponse(BaseModel):
    busy_slots: List[BusySlot]

# Схема для запроса предложений по времени
class SuggestionQuery(AvailabilityQuery): # Наследуем от AvailabilityQuery
    duration_minutes: int = Field(..., gt=0) # Требуемая длительность встречи
    # Опционально: интервал для поиска (e.g., искать только с 9 до 18)
    # search_interval_start: Optional[datetime.time] = None
    # search_interval_end: Optional[datetime.time] = None

# Схема для представления предложенного слота времени
class TimeSuggestion(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime

# Схема ответа для предложений по времени
class SuggestionResponse(BaseModel):
    suggestions: List[TimeSuggestion]

# Схема для запроса блокировки времени
class BlockTimeQuery(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime
    title: str = "Blocked Time"
    calendar_id: Optional[int] = None # В каком календаре блокировать (если не указан, то в основном) 