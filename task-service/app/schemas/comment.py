# task-service/app/schemas/comment.py
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field

# Базовая схема комментария
class CommentBase(BaseModel):
    content: str = Field(..., description="Содержание комментария")

# Схема для создания комментария
# task_id и author_user_id будут добавлены в CRUD/API
class CommentCreate(CommentBase):
    pass

# Схема для обновления комментария
class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Новое содержание комментария")

# Схема комментария из БД
class CommentInDBBase(CommentBase):
    id: int
    task_id: int
    author_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# Схема для возврата из API
class Comment(CommentInDBBase):
    pass

# Схема для внутреннего использования
class CommentInDB(CommentInDBBase):
    pass 