# company-service/app/schemas/news.py

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Базовая схема для Новостей/Объявлений
class NewsBase(BaseModel):
    title: str = Field(..., max_length=255, description="Заголовок новости")
    content: str = Field(..., description="Содержание новости (поддерживает форматирование)")
    target_department_id: Optional[int] = Field(None, description="ID целевого подразделения (если пусто - для всей компании)")
    # target_role: Optional[MembershipRole] = Field(None, ...) # Если нужно таргетирование по ролям
    media_attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Медиа-вложения (например, [{'type': 'image', 'url': '...'}])")

# Схема для создания новой Новости
class NewsCreate(NewsBase):
    # company_id и author_user_id будут установлены сервером
    published_at: Optional[datetime] = Field(None, description="Время отложенной публикации (UTC)")
    is_published: Optional[bool] = Field(True, description="Опубликовать сразу или сохранить как черновик")

# Схема для обновления Новости
class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Заголовок новости")
    content: Optional[str] = Field(None, description="Содержание новости")
    target_department_id: Optional[int] = Field(None, description="ID целевого подразделения")
    media_attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Медиа-вложения")
    is_published: Optional[bool] = Field(None, description="Статус публикации")
    published_at: Optional[datetime] = Field(None, description="Время отложенной публикации (UTC)")
    is_archived: Optional[bool] = Field(None, description="Архивировать/разархивировать новость")

# Схема для возврата данных о Новости из API
class News(NewsBase):
    id: int = Field(..., description="Уникальный идентификатор новости")
    company_id: int = Field(..., description="ID компании")
    author_user_id: Optional[int] = Field(None, description="ID автора новости (из User Service)")
    is_published: bool = Field(..., description="Опубликована ли новость")
    published_at: Optional[datetime] = Field(None, description="Фактическое или запланированное время публикации")
    is_archived: bool = Field(..., description="Архивирована ли новость")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    model_config = {"from_attributes": True} 