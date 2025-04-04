from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Импортируем Enum из модели
from app.models.membership import MembershipRole, MembershipStatus

# Базовая схема для Членства
class MembershipBase(BaseModel):
    user_id: int = Field(..., description="ID пользователя (из User Service)")
    # company_id будет браться из URL
    department_id: Optional[int] = Field(None, description="ID подразделения (если применимо)")
    role: MembershipRole = Field(..., description="Роль пользователя в компании")

# Схема для добавления нового члена команды (данные из запроса)
# Часто это делается через принятие приглашения, но может быть и прямой эндпоинт
class MembershipCreate(MembershipBase):
    status: Optional[MembershipStatus] = Field(MembershipStatus.ACTIVE, description="Начальный статус членства")

# Схема для обновления данных о членстве (например, смена роли, отдела, статуса)
class MembershipUpdate(BaseModel):
    department_id: Optional[int] = Field(None, description="Новый ID подразделения")
    role: Optional[MembershipRole] = Field(None, description="Новая роль пользователя")
    status: Optional[MembershipStatus] = Field(None, description="Новый статус членства (активен/неактивен)")

# Схема для возврата данных о членстве из API
class Membership(MembershipBase):
    id: int = Field(..., description="Уникальный идентификатор членства")
    company_id: int = Field(..., description="ID компании")
    status: MembershipStatus = Field(..., description="Текущий статус членства")
    join_date: datetime = Field(..., description="Дата присоединения к компании")
    created_at: datetime = Field(..., description="Время создания записи")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    # Опционально: можно добавить базовую информацию о пользователе, полученную из User Service
    # user_info: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True} 