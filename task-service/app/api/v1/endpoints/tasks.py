# task-service/app/api/v1/endpoints/tasks.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app import schemas, models
from app.api import deps
from app.crud import crud_task
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: schemas.TaskCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
    # company_id нужно получать либо из токена, либо через запрос к Company Service
    # Пока заглушка - предполагаем, что ID компании передается (небезопасно)
    company_id: int = Query(..., description="ID компании (временная заглушка)")
) -> Any:
    """Создает новую задачу."""
    # TODO: Проверить права пользователя на создание задачи в этой компании (запрос к Company Service)
    # TODO: Проверить существование assignee_user_id и department_id (если указаны)
    task = crud_task.create_with_owner_and_company(
        db=db, obj_in=task_in, creator_user_id=current_user_id, company_id=company_id
    )
    return task

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    assignee_user_id: Optional[int] = Query(None, description="Фильтр по ID исполнителя"),
    creator_user_id: Optional[int] = Query(None, description="Фильтр по ID создателя"),
    status: Optional[schemas.TaskStatus] = Query(None, description="Фильтр по статусу"),
    priority: Optional[schemas.TaskPriority] = Query(None, description="Фильтр по приоритету"),
    # company_id нужно получать либо из токена, либо через запрос к Company Service
    # Пока заглушка
    company_id: int = Query(..., description="ID компании (временная заглушка)"),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Получает список задач с фильтрацией."""
    # TODO: Проверить права пользователя на просмотр задач этой компании
    tasks = crud_task.get_multi_by_company(
        db, 
        company_id=company_id, 
        assignee_user_id=assignee_user_id,
        creator_user_id=creator_user_id,
        status=status,
        priority=priority,
        skip=skip, 
        limit=limit
    )
    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи"),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Получает информацию о конкретной задаче."""
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    # TODO: Проверить права пользователя на просмотр этой задачи (принадлежность к компании)
    # if task.company_id != user_company_id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")
    return task

@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    *,
    # Передаем user_id в get_db для слушателя истории
    current_user_id: int = Depends(deps.get_current_user_id),
    db: Session = Depends(lambda user_id=Depends(deps.get_current_user_id): get_db(user_id=user_id)), 
    task_id: int = Path(..., description="ID задачи"),
    task_in: schemas.TaskUpdate,
    # current_user_id: int = Depends(deps.get_current_user_id), # Уже получаем выше
    company_id: int = Depends(deps.get_current_company_id),
    current_role: str = Depends(deps.get_current_user_role),
) -> Any:
    """Обновляет задачу (доступно менеджеру/админу, создателю или исполнителю)."""
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")

    # Проверка прав на обновление
    is_manager_or_admin = current_role in [deps.MembershipRole.MANAGER, deps.MembershipRole.ADMIN]
    is_creator = task.creator_user_id == current_user_id
    is_assignee = task.assignee_user_id == current_user_id

    if not (is_manager_or_admin or is_creator or is_assignee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на обновление этой задачи")

    # TODO: Проверить assignee_user_id, department_id при изменении (их существование в нужной компании)
    updated_task = crud_task.update(
        db=db, 
        db_obj=task, 
        obj_in=task_in, 
        modifier_user_id=current_user_id
    )
    # Слушатель before_task_update должен был добавить записи в TaskHistory перед commit
    return updated_task

@router.delete("/{task_id}", response_model=schemas.Task)
def archive_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи"),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Архивирует (мягко удаляет) задачу."""
    task = crud_task.get(db=db, id=task_id) # Проверяем существование перед архивацией
    if not task or task.is_deleted:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена или уже архивирована")
    # TODO: Проверить права на архивацию
    archived_task = crud_task.archive(db=db, task_id=task_id)
    if not archived_task: # Доп. проверка, если archive вернул None
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не удалось архивировать задачу")
    return archived_task

@router.post("/{task_id}/restore", response_model=schemas.Task)
def restore_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи"),
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """Восстанавливает задачу из архива."""
    # TODO: Проверить права на восстановление
    restored_task = crud_task.restore(db=db, task_id=task_id)
    if not restored_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена в архиве или произошла ошибка")
    return restored_task 