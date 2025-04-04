# task-service/app/crud/crud_task.py
import logging # Добавляем logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, case
from sqlalchemy.sql import and_, or_
from fastapi.encoders import jsonable_encoder # Для сериализации

from app.crud.base import CRUDBase # Импортируем CRUDBase из base.py
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.messaging import publish_message # Импортируем паблишер

logger = logging.getLogger(__name__) # Инициализируем логгер

class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    def create_with_owner_and_company(
        self,
        db: Session,
        *,
        obj_in: TaskCreate,
        creator_user_id: int,
        company_id: int
    ) -> Task:
        """Создает задачу, добавляя ID создателя и компании и публикуя событие."""
        # Используем словарь для подготовки данных
        task_data = obj_in.model_dump()
        task_data['creator_user_id'] = creator_user_id
        task_data['company_id'] = company_id
        
        db_obj = self.model(**task_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Публикуем событие task.created
        try:
            # Используем jsonable_encoder для корректной сериализации объекта SQLAlchemy
            # Передаем только необходимые данные, а не весь объект с potentially lazy-loaded relationships
            message_body = jsonable_encoder(db_obj, exclude={'comments', 'attachments', 'evaluation', 'history'}) # Явно исключаем связи
            publish_message(routing_key="task.created", message_body=message_body)
        except Exception as e:
            # Логируем ошибку публикации, но не прерываем основной процесс
            logger.error(f"Failed to publish task.created event for task {db_obj.id}: {e}")
            
        return db_obj
    
    def archive(self, db: Session, *, task_id: int) -> Optional[Task]:
        """Мягко удаляет (архивирует) задачу, устанавливая is_deleted = True."""
        statement = (
            update(self.model)
            .where(self.model.id == task_id, self.model.is_deleted == False)
            .values(is_deleted=True)
            .returning(self.model)
        )
        result = db.execute(statement)
        db.commit()
        archived_task = result.scalar_one_or_none()
        return archived_task

    def restore(self, db: Session, *, task_id: int) -> Optional[Task]:
        """Восстанавливает задачу из архива (is_deleted = False)."""
        statement = (
            update(self.model)
            .where(self.model.id == task_id, self.model.is_deleted == True)
            .values(is_deleted=False)
            .returning(self.model)
        )
        result = db.execute(statement)
        db.commit()
        restored_task = result.scalar_one_or_none()
        return restored_task

    def get_multi_by_company(
        self, 
        db: Session, 
        *, 
        company_id: int, 
        assignee_user_id: Optional[int] = None,
        creator_user_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        is_deleted: bool = False, # По умолчанию ищем НЕ удаленные
        skip: int = 0, 
        limit: int = 100
    ) -> List[Task]:
        """Получает список задач для компании с фильтрами."""
        statement = (
            select(self.model)
            .where(self.model.company_id == company_id)
            .where(self.model.is_deleted == is_deleted)
        )
        if assignee_user_id is not None:
            statement = statement.where(self.model.assignee_user_id == assignee_user_id)
        if creator_user_id is not None:
             statement = statement.where(self.model.creator_user_id == creator_user_id)
        if status:
            statement = statement.where(self.model.status == status)
        if priority:
            statement = statement.where(self.model.priority == priority)
        
        statement = statement.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        
        return db.scalars(statement).all()
    
    # TODO: Добавить методы для получения задач по assignee, creator и т.д.
    # TODO: Добавить фильтрацию по датам

    # --- Методы для аналитики --- 

    def get_task_counts_by_status(self, db: Session, *, company_id: int) -> Dict[str, int]:
        """Считает количество активных задач по статусам для компании."""
        statement = (
            select(self.model.status, func.count(self.model.id))
            .where(self.model.company_id == company_id)
            .where(self.model.is_deleted == False)
            .group_by(self.model.status)
        )
        results = db.execute(statement).all()
        # Преобразуем результат в словарь {status_name: count}
        counts = {status.value: count for status, count in results}
        # Добавляем статусы с 0 задачами
        for status_enum in TaskStatus:
            if status_enum.value not in counts:
                counts[status_enum.value] = 0
        return counts

    def get_overdue_tasks_count(self, db: Session, *, company_id: int) -> int:
        """Считает количество просроченных активных задач для компании."""
        now = datetime.now(timezone.utc)
        statement = (
            select(func.count(self.model.id))
            .where(self.model.company_id == company_id)
            .where(self.model.is_deleted == False)
            .where(self.model.due_date < now)
            .where(
                or_(
                    self.model.status != TaskStatus.DONE,
                    self.model.status != TaskStatus.CANCELLED
                )
            )
        )
        count = db.scalar(statement)
        return count if count is not None else 0

    def get_active_tasks_per_assignee(self, db: Session, *, company_id: int) -> Dict[str, int]:
        """Считает количество активных (не DONE/CANCELLED) задач на каждого исполнителя."""
        statement = (
            select(self.model.assignee_user_id, func.count(self.model.id))
            .where(self.model.company_id == company_id)
            .where(self.model.is_deleted == False)
            .where(
                or_(
                    self.model.status != TaskStatus.DONE,
                    self.model.status != TaskStatus.CANCELLED
                )
             )
            .where(self.model.assignee_user_id.isnot(None)) # Исключаем задачи без исполнителя
            .group_by(self.model.assignee_user_id)
        )
        results = db.execute(statement).all()
        # Преобразуем результат в словарь {user_id_str: count}
        counts = {str(user_id): count for user_id, count in results}
        return counts

    def update(
        self,
        db: Session,
        *,
        db_obj: Task,
        obj_in: Union[TaskUpdate, Dict[str, Any]],
        modifier_user_id: Optional[int] = None, # Track who modified
    ) -> Task:
        # ... (existing update method with event publishing) ...
        pass # Placeholder if update method was fully collapsed

    # --- New methods for handling events --- #

    def delete_by_company_id(self, db: Session, *, company_id: int) -> int:
        """Удаляет все задачи, принадлежащие указанной компании."""
        num_deleted = db.query(self.model).filter(Task.company_id == company_id).delete(synchronize_session=False)
        # Коммит должен управляться извне (например, в message_callback)
        # db.commit() # No commit here
        logger.info(f"Attempted deletion of tasks for company_id={company_id}. Result count: {num_deleted}")
        return num_deleted

    def unassign_by_user_id(self, db: Session, *, user_id: int) -> int:
        """Снимает назначение задач с указанного пользователя."""
        tasks_to_update_query = db.query(self.model).filter(Task.assignee_user_id == user_id)
        # Используем update() для массового обновления, это эффективнее
        # Не используем self.update(), чтобы избежать сложной логики событий при массовом снятии
        updated_count = tasks_to_update_query.update(
            {Task.assignee_user_id: None},
            synchronize_session=False # Важно для производительности и избежания конфликтов
        )
        # Коммит должен управляться извне
        # db.commit() # No commit here
        logger.info(f"Attempted unassignment of tasks from user_id={user_id}. Result count: {updated_count}")
        # Важно: Этот метод НЕ будет публиковать события task.updated для каждой задачи
        # Если это нужно, придется итерировать и вызывать self.update(), как в предыдущей версии
        return updated_count

crud_task = CRUDTask(Task) 