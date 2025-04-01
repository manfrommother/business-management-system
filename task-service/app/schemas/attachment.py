# task-service/app/schemas/attachment.py
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

# Базовая схема вложения (для ответа API)
class AttachmentBase(BaseModel):
    filename: str = Field(..., description="Имя файла")
    content_type: str = Field(..., description="MIME тип")
    file_size: int = Field(..., description="Размер файла в байтах")

# Схема для внутреннего создания (добавляем путь и ID загрузившего)
class AttachmentCreateInternal(AttachmentBase):
    file_path: str
    uploader_user_id: int
    task_id: Optional[int] = None
    comment_id: Optional[int] = None

# Схема вложения из БД (добавляем ID и таймстемпы)
class AttachmentInDBBase(AttachmentBase):
    id: int
    file_path: str # Путь может быть нужен для внутренних операций
    uploader_user_id: int
    task_id: Optional[int] = None
    comment_id: Optional[int] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

# Финальная схема для возврата из API
# Обычно не возвращаем file_path наружу
class Attachment(AttachmentInDBBase):
    file_path: Optional[str] = Field(None, exclude=True) # Исключаем file_path из ответа 