# task-service/app/schemas/task.py
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

# Импортируем Enum из моделей
from app.models.task import TaskStatus, TaskPriority

# Общая база для Task - поля, общие для создания и чтения
class TaskBase(BaseModel):
    title: str = Field(..., max_length=255, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    assignee_user_id: Optional[int] = Field(None, description="ID исполнителя")
    department_id: Optional[int] = Field(None, description="ID отдела (опционально)")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="Статус задачи")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Приоритет задачи")
    start_date: Optional[datetime] = Field(None, description="Дата начала работы (UTC)")
    due_date: Optional[datetime] = Field(None, description="Срок выполнения (UTC)")

# Схема для создания задачи (наследуется от TaskBase)
# Здесь могут быть поля, которые не возвращаются API (если нужно)
# creator_user_id и company_id обычно добавляются в CRUD на основе данных запроса/токена
class TaskCreate(TaskBase):
    pass # На данный момент дополнительных полей нет

# Схема для обновления задачи (все поля опциональны)
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Название задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    assignee_user_id: Optional[int] = Field(None, description="ID исполнителя")
    department_id: Optional[int] = Field(None, description="ID отдела (опционально)")
    status: Optional[TaskStatus] = Field(None, description="Статус задачи")
    priority: Optional[TaskPriority] = Field(None, description="Приоритет задачи")
    start_date: Optional[datetime] = Field(None, description="Дата начала работы (UTC)")
    due_date: Optional[datetime] = Field(None, description="Срок выполнения (UTC)")
    completion_date: Optional[datetime] = Field(None, description="Фактическая дата выполнения (UTC)")
    # is_deleted обычно управляется через DELETE эндпоинт

# Базовая схема для данных из БД (включает ID и таймстемпы)
class TaskInDBBase(TaskBase):
    id: int
    creator_user_id: int
    company_id: int
    completion_date: Optional[datetime] = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 config:
    # from_attributes=True заменяет orm_mode=True
    model_config = {
        "from_attributes": True
    }

# Финальная схема для возврата из API (наследуется от TaskInDBBase)
class Task(TaskInDBBase):
    pass # На данный момент дополнительных полей нет

# Схема для внутреннего использования (если нужно отделить от API)
class TaskInDB(TaskInDBBase):
    pass 