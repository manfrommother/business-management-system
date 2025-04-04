# task-service/app/api/v1/endpoints/evaluations.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, models # Добавляем models
from app.api import deps
from app.crud import crud_evaluation, crud_task # Добавляем crud_task
from app.db.session import get_db
from app.models.task import TaskStatus # Для проверки статуса задачи

# Создаем два роутера:
# - один для действий в контексте задачи (/tasks/{task_id}/evaluate)
# - другой для получения списков оценок по пользователю/отделу
evaluate_task_router = APIRouter()
evaluations_list_router = APIRouter()

# --- Эндпоинт /tasks/{task_id}/evaluate --- 

@evaluate_task_router.post("/", response_model=schemas.Evaluation, status_code=status.HTTP_201_CREATED)
def evaluate_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи для оценки"),
    evaluation_in: schemas.EvaluationCreate,
    evaluator_user_id: int = Depends(deps.get_current_user_id), # ID оценщика
    company_id: int = Depends(deps.get_current_company_id), # Компания оценщика
    # Требуем роль менеджера или админа для оценки
    _ = Depends(deps.require_manager_or_admin),
) -> Any:
    """Оценивает выполненную задачу (доступно менеджерам и админам)."""
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")

    # Проверка: оценивать можно только завершенные задачи?
    # Или задачи в статусе REVIEW? По ТЗ неясно, пока разрешим для DONE.
    if task.status != TaskStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Оценивать можно только задачи со статусом '{TaskStatus.DONE}'. Текущий статус: '{task.status}'"
        )
        
    # Проверка: может ли этот пользователь (менеджер/админ) оценивать эту задачу?
    # Например, является ли он руководителем исполнителя или создателя?
    # TODO: Добавить эту проверку, если требуется более строгий контроль.
    # Пока предполагаем, что любой менеджер/админ компании может оценить любую завершенную задачу.

    try:
        evaluation = crud_evaluation.create_for_task(
            db=db, 
            obj_in=evaluation_in, 
            evaluator_user_id=evaluator_user_id, 
            task_id=task_id
        )
    except ValueError as e: # Перехватываем ошибку, если задача уже оценена
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=str(e)
        )
    except Exception as e: # Другие возможные ошибки БД
        # Логирование ошибки
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при сохранении оценки")
        
    return evaluation

# --- Эндпоинты для получения списков оценок --- 

@evaluations_list_router.get("/users/{user_id}/evaluations", response_model=List[schemas.Evaluation])
def read_user_evaluations(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., description="ID пользователя, чьи оценки задач нужно получить"),
    skip: int = 0,
    limit: int = 100,
    requester_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id),
    requester_role: str = Depends(deps.get_current_user_role),
) -> Any:
    """Получает список оценок задач, выполненных указанным пользователем."""
    # Проверка прав: 
    # - Сам пользователь может видеть свои оценки.
    # - Менеджер/админ может видеть оценки любого пользователя в своей компании.
    # TODO: Проверить, принадлежит ли user_id к company_id (нужен запрос к Company Service?).
    is_self = requester_user_id == user_id
    is_manager_or_admin = requester_role in [deps.MembershipRole.MANAGER, deps.MembershipRole.ADMIN]
    
    if not (is_self or is_manager_or_admin):
        # TODO: Более точная проверка - является ли запрашивающий руководитель указанного user_id?
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на просмотр оценок этого пользователя")

    evaluations = crud_evaluation.get_multi_by_user(
        db=db, user_id=user_id, company_id=company_id, skip=skip, limit=limit
    )
    return evaluations

@evaluations_list_router.get("/departments/{department_id}/evaluations", response_model=List[schemas.Evaluation])
def read_department_evaluations(
    *,
    db: Session = Depends(get_db),
    department_id: int = Path(..., description="ID отдела, оценки задач которого нужно получить"),
    skip: int = 0,
    limit: int = 100,
    company_id: int = Depends(deps.get_current_company_id),
     # Требуем менеджера или админа для просмотра оценок отдела
    _ = Depends(deps.require_manager_or_admin),
) -> Any:
    """Получает список оценок задач в указанном отделе (доступно менеджерам/админам)."""
    # Права проверены зависимостью
    # TODO: Проверить, принадлежит ли department_id к company_id (нужен запрос к Company Service?).
    
    evaluations = crud_evaluation.get_multi_by_department(
        db=db, department_id=department_id, company_id=company_id, skip=skip, limit=limit
    )
    return evaluations 