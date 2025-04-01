# task-service/app/api/v1/endpoints/comments.py
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, models # Добавляем models
from app.api import deps
from app.crud import crud_comment, crud_task # Добавляем crud_task
from app.db.session import get_db

# Создаем два роутера:
# - один для действий с комментариями в контексте задачи (/tasks/{task_id}/comments)
# - другой для действий с конкретным комментарием по его ID (/comments/{comment_id})
task_comments_router = APIRouter()
comments_router = APIRouter()

# --- Эндпоинты /tasks/{task_id}/comments --- 

@task_comments_router.post("/", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
def create_comment_for_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи, к которой добавляется комментарий"),
    comment_in: schemas.CommentCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id), # Проверяем компанию
) -> Any:
    """Добавляет комментарий к задаче."""
    # Проверяем, существует ли задача и принадлежит ли она компании пользователя
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")
    # TODO: Дополнительная проверка прав - может ли пользователь комментировать эту задачу?
    #       (Например, является ли он создателем, исполнителем, или просто участником компании?)
    #       Пока разрешаем всем участникам компании.

    comment = crud_comment.create_with_author_and_task(
        db=db, obj_in=comment_in, author_user_id=current_user_id, task_id=task_id
    )
    return comment

@task_comments_router.get("/", response_model=List[schemas.Comment])
def read_task_comments(
    *,
    db: Session = Depends(get_db),
    task_id: int = Path(..., description="ID задачи, комментарии которой нужно получить"),
    skip: int = 0,
    limit: int = 100,
    company_id: int = Depends(deps.get_current_company_id), # Проверяем компанию
    _ = Depends(deps.get_current_user_id) # Проверяем аутентификацию
) -> Any:
    """Получает список комментариев к задаче."""
    # Проверяем, существует ли задача и принадлежит ли она компании пользователя
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")
    # TODO: Проверка прав на просмотр комментов (аналогично create)
    
    comments = crud_comment.get_multi_by_task(
        db=db, task_id=task_id, skip=skip, limit=limit
    )
    return comments

# --- Эндпоинты /comments/{comment_id} --- 

@comments_router.put("/{comment_id}", response_model=schemas.Comment)
def update_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., description="ID комментария для обновления"),
    comment_in: schemas.CommentUpdate,
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id), # Для доп. проверки
) -> Any:
    """Обновляет комментарий (только автор)."""
    comment = crud_comment.get(db=db, id=comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")
    
    # Проверяем, принадлежит ли комментарий текущему пользователю
    if comment.author_user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не можете редактировать этот комментарий")
        
    # Дополнительная проверка: принадлежит ли задача комментария компании пользователя
    # (хотя если пользователь - автор, это должно выполняться автоматически, но для надежности)
    task = crud_task.get(db=db, id=comment.task_id)
    if not task or task.company_id != company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка доступа к задаче комментария")

    updated_comment = crud_comment.update(db=db, db_obj=comment, obj_in=comment_in)
    return updated_comment

@comments_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = Path(..., description="ID комментария для удаления"),
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id), # Для доп. проверки
    current_role: str = Depends(deps.get_current_user_role) # Для проверки прав админа/менеджера
) -> None:
    """Удаляет комментарий (автор или админ/менеджер)."""
    comment = crud_comment.get(db=db, id=comment_id)
    if not comment:
        # Возвращаем 204, даже если комментарий не найден, чтобы сделать операцию идемпотентной
        return None # Или можно возвращать 404, если не найден

    # Проверяем права на удаление
    is_author = comment.author_user_id == current_user_id
    is_manager_or_admin = current_role in [deps.MembershipRole.MANAGER, deps.MembershipRole.ADMIN]

    if not (is_author or is_manager_or_admin):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление этого комментария")
         
    # Дополнительная проверка: принадлежит ли задача комментария компании пользователя
    task = crud_task.get(db=db, id=comment.task_id)
    if not task or task.company_id != company_id:
         # Если задача не принадлежит компании, админ/менеджер не должен иметь возможность удалить коммент
         if is_manager_or_admin and not is_author:
              raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Администратор/Менеджер не может удалить комментарий к задаче из другой компании")
         # Если автор - тоже ошибка (странная ситуация)
         elif is_author:
              raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка доступа к задаче комментария")

    crud_comment.remove(db=db, id=comment_id)
    return None # Возвращаем None для статуса 204 