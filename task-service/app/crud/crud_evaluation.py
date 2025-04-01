# task-service/app/crud/crud_evaluation.py
from typing import List, Optional
import logging # Добавляем logging

from sqlalchemy.orm import Session
from sqlalchemy import select, func, cast, Float # Добавляем cast, Float

from app.crud.base import CRUDBase
from app.models.evaluation import Evaluation
from app.models.task import Task # Нужна модель Task для join
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate
from app.schemas.analytics import AverageScores # Импортируем схему
from app.core.messaging import publish_message # Импортируем паблишер
from fastapi.encoders import jsonable_encoder # Для сериализации

logger = logging.getLogger(__name__)

class CRUDEvaluation(CRUDBase[Evaluation, EvaluationCreate, EvaluationUpdate]):

    def get_by_task(self, db: Session, *, task_id: int) -> Optional[Evaluation]:
        """Получает оценку для конкретной задачи (если она есть)."""
        statement = select(self.model).where(self.model.task_id == task_id)
        return db.scalars(statement).first()

    def create_for_task(
        self,
        db: Session,
        *,
        obj_in: EvaluationCreate,
        evaluator_user_id: int,
        task_id: int
    ) -> Evaluation:
        """Создает оценку для задачи, проверяя, что она еще не оценена."""
        # Проверка, что оценка для этой задачи еще не существует
        existing_evaluation = self.get_by_task(db=db, task_id=task_id)
        if existing_evaluation:
            # Можно либо возвращать ошибку, либо обновлять существующую
            # По ТЗ неясно, пока возвращаем ошибку.
            raise ValueError(f"Task {task_id} has already been evaluated.")
            
        db_obj = self.model(
            **obj_in.model_dump(),
            evaluator_user_id=evaluator_user_id,
            task_id=task_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Публикуем событие task.evaluated
        try:
            # Получаем данные связанной задачи для сообщения
            task = db_obj.task # Получаем Task через relationship
            message_body = {
                "evaluation_id": db_obj.id,
                "task_id": task_id,
                "evaluator_user_id": evaluator_user_id,
                "assignee_user_id": task.assignee_user_id if task else None,
                "company_id": task.company_id if task else None,
                "scores": {
                    "timeliness": db_obj.timeliness_score,
                    "quality": db_obj.quality_score,
                    "completeness": db_obj.completeness_score
                }
                # Добавляем оценку, если нужно
                # "evaluation_details": jsonable_encoder(db_obj)
            }
            publish_message(routing_key="task.evaluated", message_body=message_body)
        except Exception as e:
            logger.error(f"Failed to publish task.evaluated event for task {task_id}: {e}")
            
        return db_obj

    # Методы для получения списков оценок (для аналитики/отчетов)
    def get_multi_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int, # ID пользователя, чьи оценки (как исполнителя) ищем
        company_id: int, # В рамках какой компании
        skip: int = 0, 
        limit: int = 100
    ) -> List[Evaluation]:
        """Получает оценки задач, назначенных указанному пользователю в компании."""
        statement = (
            select(self.model)
            .join(Task, self.model.task_id == Task.id)
            .where(Task.assignee_user_id == user_id)
            .where(Task.company_id == company_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.scalars(statement).all()
        
    def get_multi_by_department(
        self,
        db: Session,
        *,
        department_id: int,
        company_id: int, # Доп. проверка компании
        skip: int = 0,
        limit: int = 100
    ) -> List[Evaluation]:
        """Получает оценки задач в указанном отделе компании."""
        statement = (
            select(self.model)
            .join(Task, self.model.task_id == Task.id)
            .where(Task.department_id == department_id)
            .where(Task.company_id == company_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return db.scalars(statement).all()
        
    # --- Методы для аналитики --- 

    def get_average_scores(
        self,
        db: Session,
        *,
        company_id: int,
        department_id: Optional[int] = None,
        user_id: Optional[int] = None # ID исполнителя (assignee)
    ) -> AverageScores:
        """Считает средние оценки для компании, отдела или пользователя."""
        statement = select(
            func.count(self.model.id).label("total_evaluated"),
            # Используем cast(..., Float) для PostgreSQL для корректного деления
            func.avg(cast(self.model.timeliness_score, Float)).label("avg_timeliness"),
            func.avg(cast(self.model.quality_score, Float)).label("avg_quality"),
            func.avg(cast(self.model.completeness_score, Float)).label("avg_completeness")
        ).join(Task, self.model.task_id == Task.id)
        
        # Фильтруем по компании обязательно
        statement = statement.where(Task.company_id == company_id)
        
        # Добавляем фильтры по отделу или пользователю, если они указаны
        if department_id is not None:
            statement = statement.where(Task.department_id == department_id)
        if user_id is not None:
            statement = statement.where(Task.assignee_user_id == user_id)
            
        result = db.execute(statement).first()
        
        if result and result.total_evaluated > 0:
            # Pydantic ожидает float, SQLAlchemy avg может вернуть Decimal, преобразуем
            return AverageScores(
                total_evaluated=result.total_evaluated,
                avg_timeliness=float(result.avg_timeliness) if result.avg_timeliness else None,
                avg_quality=float(result.avg_quality) if result.avg_quality else None,
                avg_completeness=float(result.avg_completeness) if result.avg_completeness else None
            )
        else:
            # Если оценок нет, возвращаем нули
            return AverageScores(total_evaluated=0)

crud_evaluation = CRUDEvaluation(Evaluation) 