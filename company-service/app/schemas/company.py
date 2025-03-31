# company-service/app/schemas/company.py

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl

from app.models.company import CompanyStatus # Импортируем Enum из модели

# Общие поля, присутствующие во всех схемах Company
class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255, description="Название компании")
    description: Optional[str] = Field(None, description="Описание компании")
    contact_info: Optional[str] = Field(None, description="Контактная информация")
    logo_url: Optional[HttpUrl] = Field(None, description="URL логотипа")
    timezone: Optional[str] = Field("UTC", max_length=100, description="Временная зона")
    working_hours: Optional[str] = Field(None, max_length=255, description="Рабочие часы")
    corporate_colors: Optional[Dict[str, str]] = Field(None, description="Корпоративные цвета (JSON)")

# Схема для создания новой компании (данные из запроса)
class CompanyCreate(CompanyBase):
    # Возможно, добавить owner_user_id, если он обязателен при создании
    pass

# Схема для обновления компании (данные из запроса)
class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название компании")
    description: Optional[str] = Field(None, description="Описание компании")
    contact_info: Optional[str] = Field(None, description="Контактная информация")
    logo_url: Optional[HttpUrl] = Field(None, description="URL логотипа")
    timezone: Optional[str] = Field(None, max_length=100, description="Временная зона")
    working_hours: Optional[str] = Field(None, max_length=255, description="Рабочие часы")
    corporate_colors: Optional[Dict[str, str]] = Field(None, description="Корпоративные цвета (JSON)")
    status: Optional[CompanyStatus] = Field(None, description="Статус компании") # Позволяем менять статус

# Схема для возврата данных о компании из API (включая ID и т.д.)
class Company(CompanyBase):
    id: int = Field(..., description="Уникальный идентификатор компании")
    status: CompanyStatus = Field(..., description="Текущий статус компании")
    is_deleted: bool = Field(..., description="Флаг мягкого удаления")
    deleted_at: Optional[datetime] = Field(None, description="Время мягкого удаления")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    model_config = {"from_attributes": True}

# Схема для представления компании в списке (можно убрать лишние поля)
class CompanyInList(BaseModel):
    id: int
    name: str
    status: CompanyStatus
    logo_url: Optional[HttpUrl] = None

    model_config = {"from_attributes": True}

# Схема для возврата статистики по компании
class DepartmentMemberCount(BaseModel):
    department_id: Optional[int] # -1 для сотрудников без отдела
    department_name: str
    member_count: int

class CompanyStats(BaseModel):
    total_members: int = Field(..., description="Общее количество активных участников")
    pending_invitations: int = Field(..., description="Количество активных приглашений")
    published_news: int = Field(..., description="Количество опубликованных новостей")
    members_by_department: List[DepartmentMemberCount] = Field(..., description="Распределение участников по отделам") 