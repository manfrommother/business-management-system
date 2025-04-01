# task-service/app/crud/crud_history.py
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models.history import TaskHistory
from app.schemas.history import TaskHistoryCreate, TaskHistoryUpdate # Update не используется

# Определяем фиктивную схему Update, т.к. CRUDBase требует ее тип
from pydantic import BaseModel
class TaskHistoryUpdate(BaseModel):
    pass 

class CRUDHistory(CRUDBase[TaskHistory, TaskHistoryCreate, TaskHistoryUpdate]):

    def get_multi_by_task(
        self, db: Session, *, task_id: int, skip: int = 0, limit: int = 100
    ) -> List[TaskHistory]:
        """Получает историю изменений для конкретной задачи."""
        statement = (
            select(self.model)
            .where(self.model.task_id == task_id)
            .order_by(self.model.changed_at.desc()) # Сортируем по убыванию даты
            .offset(skip)
            .limit(limit)
        )
        return db.scalars(statement).all()

crud_history = CRUDHistory(TaskHistory) 