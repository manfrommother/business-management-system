# task-service/app/crud/crud_comment.py
from typing import List, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate
from app.core.messaging import publish_message
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):

    def create_with_author_and_task(
        self,
        db: Session,
        *,
        obj_in: CommentCreate,
        author_user_id: int,
        task_id: int
    ) -> Comment:
        """Создает комментарий, добавляя ID автора и задачи."""
        db_obj = self.model(
            **obj_in.model_dump(),
            author_user_id=author_user_id,
            task_id=task_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Публикуем событие task.comment_added
        try:
            message_body = {
                "comment_id": db_obj.id,
                "task_id": task_id,
                "author_user_id": author_user_id,
                # Получаем company_id из задачи
                "company_id": db_obj.task.company_id if db_obj.task else None, 
                "content": db_obj.content,
                # Можно добавить детали задачи/автора, если нужно подписчикам
            }
            publish_message(routing_key="task.comment_added", message_body=message_body)
        except Exception as e:
            logger.error(f"Failed to publish task.comment_added event for task {task_id}, comment {db_obj.id}: {e}")
            
        return db_obj

    def get_multi_by_task(
        self, db: Session, *, task_id: int, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """Получает список комментариев для конкретной задачи."""
        statement = (
            select(self.model)
            .where(self.model.task_id == task_id)
            .order_by(self.model.created_at.asc()) # Сортируем по возрастанию даты
            .offset(skip)
            .limit(limit)
        )
        return db.scalars(statement).all()

crud_comment = CRUDComment(Comment) 