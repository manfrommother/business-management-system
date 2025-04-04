# task-service/app/schemas/history.py
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

# Базовая схема записи истории
class TaskHistoryBase(BaseModel):
    field_changed: str = Field(..., description="Название измененного поля")
    old_value: Optional[str] = Field(None, description="Старое значение")
    new_value: Optional[str] = Field(None, description="Новое значение")
    change_comment: Optional[str] = Field(None, description="Комментарий к изменению")

# Схема для внутреннего создания (добавляем ID пользователя и задачи)
class TaskHistoryCreate(TaskHistoryBase):
    user_id: int
    task_id: int

# Схема истории из БД (добавляем ID и таймстемпы)
class TaskHistoryInDBBase(TaskHistoryBase):
    id: int
    task_id: int
    user_id: int
    changed_at: datetime

    model_config = {
        "from_attributes": True
    }

# Финальная схема для возврата из API
class TaskHistory(TaskHistoryInDBBase):
    pass

# Схема для внутреннего использования
class TaskHistoryInDB(TaskHistoryInDBBase):
    pass 