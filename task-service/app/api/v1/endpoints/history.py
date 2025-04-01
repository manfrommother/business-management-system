# task-service/app/api/v1/endpoints/history.py
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.crud import crud_history, crud_task # Добавляем crud_task
from app.db.session import get_db

router = APIRouter()

@router.get("/tasks/{task_id}/history", response_model=List[schemas.TaskHistory])
def read_task_history(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи, историю которой нужно получить"),
    skip: int = 0,
    limit: int = 100,
    company_id: int = Depends(deps.get_current_company_id), # Проверяем компанию
    _ = Depends(deps.get_current_user_id) # Проверяем аутентификацию
) -> Any:
    """Получает историю изменений для задачи."""
    # Проверяем, существует ли задача и принадлежит ли она компании пользователя
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")
    # TODO: Проверка прав на просмотр истории (аналогично просмотру задачи)
    
    history = crud_history.get_multi_by_task(
        db=db, task_id=task_id, skip=skip, limit=limit
    )
    return history 