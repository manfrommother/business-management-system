from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

# Импортируем Enum из модели
from app.models.invitation import InvitationStatus
# Возможно, понадобится MembershipRole для поля role
from app.models.membership import MembershipRole

# Базовая схема для Приглашения
class InvitationBase(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email приглашаемого пользователя (если известно)")
    role: MembershipRole = Field(MembershipRole.EMPLOYEE, description="Роль, назначаемая при принятии")
    expires_at: Optional[datetime] = Field(None, description="Срок действия приглашения (UTC)")
    usage_limit: Optional[int] = Field(None, description="Лимит использований (null - безлимитно для email, 1 - по умолчанию для общих)")

# Схема для создания нового Приглашения
class InvitationCreate(InvitationBase):
    # company_id берется из URL
    # code генерируется сервером
    pass

# Схема для возврата данных о Приглашении из API
class Invitation(InvitationBase):
    id: int = Field(..., description="Уникальный идентификатор приглашения")
    code: str = Field(..., description="Уникальный код приглашения")
    company_id: int = Field(..., description="ID компании, к которой относится приглашение")
    status: InvitationStatus = Field(..., description="Текущий статус приглашения")
    times_used: int = Field(..., description="Количество использований")
    created_by_user_id: Optional[int] = Field(None, description="ID пользователя, создавшего приглашение")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    model_config = {"from_attributes": True}

# Схема для принятия приглашения
class InvitationAccept(BaseModel):
    # Обычно принятие идет по коду в URL, тело может быть пустым
    # или содержать доп. информацию, если требуется
    pass

# Схема для проверки кода приглашения
class InvitationCheck(BaseModel):
    # Аналогично, код передается в URL, тело пустое
    pass 