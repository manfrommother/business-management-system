# task-service/app/crud/base.py
import logging # Добавляем логгер
import copy # Для копирования состояния объекта
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import datetime # Добавляем datetime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base_class import Base
# Импортируем Task и TaskStatus для проверки типа и статуса
from app.models.task import Task, TaskStatus
# Импортируем публикатор сообщений
from app.core.messaging import publish_message

logger = logging.getLogger(__name__)

# Определяем типовые переменные для моделей и схем CRUD
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        statement = select(self.model).offset(skip).limit(limit).order_by(self.model.id) # Добавим сортировку по ID
        return db.scalars(statement).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        # Сохраняем старые значения *отслеживаемых* полей для Task
        old_data = {}
        is_task_model = isinstance(db_obj, Task)
        if is_task_model:
            tracked_fields = [
                "title", "description", "assignee_user_id", "department_id", 
                "status", "priority", "start_date", "due_date", "completion_date"
            ]
            for field in tracked_fields:
                old_data[field] = getattr(db_obj, field, None)

        # Применяем обновления
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        
        changed_fields = {} 
        for field in obj_data:
            if field in update_data and update_data[field] != obj_data.get(field):
                # Используем obj_data.get(field) для сравнения, т.к. он содержит сериализованные значения
                setattr(db_obj, field, update_data[field])
                if field in old_data: # Сохраняем только изменения отслеживаемых полей
                    changed_fields[field] = {
                        "old": old_data[field],
                        "new": update_data[field] # Берем новое значение из update_data
                    }

        if not changed_fields and not db.is_modified(db_obj):
             # Если не было изменений в отслеживаемых полях и объект не помечен как измененный SQLAlchemy
             return db_obj # Ничего не делаем, не коммитим, не публикуем

        db.add(db_obj) # Добавляем в сессию, даже если нет tracked changes (могли быть другие)
        db.commit()
        db.refresh(db_obj)

        # Публикация событий после успешного обновления (только для Task и если были изменения)
        if is_task_model and changed_fields:
            task_id = db_obj.id
            company_id = db_obj.company_id
            user_id = db.info.get('user_id') # Получаем ID пользователя из сессии

            # 1. Общее событие task.updated
            try:
                update_event_body = {
                    "task_id": task_id,
                    "company_id": company_id,
                    "user_id": user_id, # ID пользователя, внесшего изменения
                    "changes": jsonable_encoder(changed_fields, custom_encoder={datetime: str})
                }
                publish_message(routing_key="task.updated", message_body=update_event_body)
            except Exception as e:
                logger.error(f"Failed to publish task.updated event for task {task_id}: {e}")

            # 2. Событие task.status_changed
            if "status" in changed_fields:
                old_status = changed_fields["status"]["old"]
                new_status = changed_fields["status"]["new"]
                try:
                    status_event_body = {
                        "task_id": task_id,
                        "company_id": company_id,
                        "user_id": user_id,
                        "old_status": old_status,
                        "new_status": new_status
                    }
                    publish_message(routing_key="task.status_changed", message_body=status_event_body)
                    
                    # 3. Событие task.completed (если статус стал DONE)
                    if new_status == TaskStatus.DONE and old_status != TaskStatus.DONE:
                         try:
                              completion_event_body = {
                                   "task_id": task_id,
                                   "company_id": company_id,
                                   "user_id": user_id,
                                   "assignee_user_id": db_obj.assignee_user_id,
                                   "completion_date": db_obj.completion_date 
                              }
                              # Используем jsonable_encoder для дат
                              publish_message(routing_key="task.completed", message_body=jsonable_encoder(completion_event_body))
                         except Exception as e:
                              logger.error(f"Failed to publish task.completed event for task {task_id}: {e}")
                              
                except Exception as e:
                     logger.error(f"Failed to publish task.status_changed event for task {task_id}: {e}")

        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj 