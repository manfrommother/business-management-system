from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, validator


class TeamNewsBase(BaseModel):
    """Базовая модель для новостей команды"""
    title: str
    content: str
    department_id: Optional[uuid.UUID] = None
    is_pinned: bool = False


class TeamNewsCreate(TeamNewsBase):
    """Модель для создания новости команды"""
    pass


class TeamNewsUpdate(BaseModel):
    """Модель для обновления новости команды"""
    title: Optional[str] = None
    content: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    is_pinned: Optional[bool] = None
    
    @validator('is_pinned')
    def validate_is_pinned(cls, v):
        """Валидатор для поля is_pinned, чтобы избежать путаницы между None и False"""
        if v is None:
            # Если значение не указано, оставляем как есть
            return v
        # Преобразуем в булево значение
        return bool(v)


class TeamNewsInDB(TeamNewsBase):
    """Модель новости команды в базе данных"""
    id: uuid.UUID
    team_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True  # Позволяет использовать как snake_case, так и camelCase


class TeamNewsResponse(TeamNewsInDB):
    """Модель для ответа с новостью команды"""
    # Имя создателя новости, получаемое из внешнего сервиса пользователей
    # Это поле не присутствует в модели TeamNews, а заполняется отдельно
    creator_name: Optional[str] = None