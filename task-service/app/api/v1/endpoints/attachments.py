# task-service/app/api/v1/endpoints/attachments.py
import os
import shutil
import uuid
import logging
from pathlib import Path as FilePath # Используем Path для работы с путями
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Path as RoutePath
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import schemas, models
from app.api import deps
from app.crud import crud_attachment, crud_task, crud_comment
from app.db.session import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

# Создаем три роутера:
# - для действий в контексте задачи (/tasks/{task_id}/attachments)
# - для действий в контексте комментария (/comments/{comment_id}/attachments)
# - для прямого доступа к вложению (/attachments/{attachment_id})
task_attachments_router = APIRouter()
comment_attachments_router = APIRouter()
attachments_router = APIRouter()

# Вспомогательная функция для сохранения файла
def save_upload_file(upload_file: UploadFile, destination: FilePath) -> None:
    try:
        # Убедимся, что директория существует
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

# --- Эндпоинты для ЗАДАЧ --- 

@task_attachments_router.post("/", response_model=schemas.Attachment, status_code=status.HTTP_201_CREATED)
async def upload_attachment_for_task(
    *,
    db: Session = Depends(get_db),
    task_id: int = RoutePath(..., description="ID задачи для прикрепления файла"),
    file: UploadFile = File(..., description="Файл для загрузки"),
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id),
) -> Any:
    """Загружает файл и прикрепляет его к задаче."""
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")
    # TODO: Проверка прав на добавление вложения к этой задаче

    # Генерируем уникальное имя файла и путь
    upload_dir = FilePath(settings.UPLOAD_DIRECTORY)
    file_extension = FilePath(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    destination_path = upload_dir / unique_filename

    # Сохраняем файл
    await save_upload_file(upload_file=file, destination=destination_path)
    logger.info(f"File {file.filename} saved to {destination_path} for task {task_id}")

    # Создаем запись в БД
    attachment_in = schemas.AttachmentCreateInternal(
        filename=file.filename,
        content_type=file.content_type,
        file_path=str(destination_path.resolve()), # Сохраняем абсолютный путь?
        file_size=file.size,
        uploader_user_id=current_user_id,
        task_id=task_id,
        comment_id=None
    )
    
    try:
        attachment = crud_attachment.create(db=db, obj_in=attachment_in)
    except Exception as e:
        logger.error(f"Error creating attachment record for task {task_id}: {e}")
        # Пытаемся удалить уже сохраненный файл, если запись в БД не удалась
        try:
            os.remove(destination_path)
            logger.warning(f"Removed orphaned file {destination_path} after DB error.")
        except OSError as rm_err:
             logger.error(f"Failed to remove orphaned file {destination_path}: {rm_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сохранения информации о файле")

    return attachment

@task_attachments_router.get("/", response_model=List[schemas.Attachment])
def read_task_attachments(
    *,
    db: Session = Depends(get_db),
    task_id: int = RoutePath(..., description="ID задачи для получения вложений"),
    company_id: int = Depends(deps.get_current_company_id),
    _ = Depends(deps.get_current_user_id),
) -> Any:
    """Получает список вложений для задачи."""
    task = crud_task.get(db=db, id=task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этой задаче запрещен")
    # TODO: Проверка прав на просмотр вложений

    attachments = crud_attachment.get_multi_by_task(db=db, task_id=task_id)
    return attachments

# --- Эндпоинты для КОММЕНТАРИЕВ --- 

@comment_attachments_router.post("/", response_model=schemas.Attachment, status_code=status.HTTP_201_CREATED)
async def upload_attachment_for_comment(
    *,
    db: Session = Depends(get_db),
    comment_id: int = RoutePath(..., description="ID комментария для прикрепления файла"),
    file: UploadFile = File(..., description="Файл для загрузки"),
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id),
) -> Any:
    """Загружает файл и прикрепляет его к комментарию."""
    comment = crud_comment.get(db=db, id=comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")
    
    # Проверяем доступ к задаче комментария
    task = crud_task.get(db=db, id=comment.task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача комментария не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к задаче комментария запрещен")
    # TODO: Проверка прав на добавление вложения к этому комментарию

    # Логика сохранения файла и создания записи - аналогична task
    upload_dir = FilePath(settings.UPLOAD_DIRECTORY)
    file_extension = FilePath(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    destination_path = upload_dir / unique_filename

    await save_upload_file(upload_file=file, destination=destination_path)
    logger.info(f"File {file.filename} saved to {destination_path} for comment {comment_id}")

    attachment_in = schemas.AttachmentCreateInternal(
        filename=file.filename,
        content_type=file.content_type,
        file_path=str(destination_path.resolve()),
        file_size=file.size,
        uploader_user_id=current_user_id,
        task_id=None,
        comment_id=comment_id
    )
    
    try:
        attachment = crud_attachment.create(db=db, obj_in=attachment_in)
    except Exception as e:
        logger.error(f"Error creating attachment record for comment {comment_id}: {e}")
        try:
            os.remove(destination_path)
            logger.warning(f"Removed orphaned file {destination_path} after DB error.")
        except OSError as rm_err:
             logger.error(f"Failed to remove orphaned file {destination_path}: {rm_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка сохранения информации о файле")

    return attachment

@comment_attachments_router.get("/", response_model=List[schemas.Attachment])
def read_comment_attachments(
    *,
    db: Session = Depends(get_db),
    comment_id: int = RoutePath(..., description="ID комментария для получения вложений"),
    company_id: int = Depends(deps.get_current_company_id),
    _ = Depends(deps.get_current_user_id),
) -> Any:
    """Получает список вложений для комментария."""
    comment = crud_comment.get(db=db, id=comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден")

    # Проверяем доступ к задаче комментария
    task = crud_task.get(db=db, id=comment.task_id)
    if not task or task.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача комментария не найдена")
    if task.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к задаче комментария запрещен")
    # TODO: Проверка прав на просмотр вложений комментария

    attachments = crud_attachment.get_multi_by_comment(db=db, comment_id=comment_id)
    return attachments

# --- Эндпоинты для прямого доступа --- 

@attachments_router.get("/{attachment_id}/download")
async def download_attachment(
    *,
    db: Session = Depends(get_db),
    attachment_id: int = RoutePath(..., description="ID вложения для скачивания"),
    company_id: int = Depends(deps.get_current_company_id),
    _ = Depends(deps.get_current_user_id),
) -> FileResponse:
    """Скачивает файл вложения."""
    attachment = crud_attachment.get(db=db, id=attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вложение не найдено")

    # Проверяем доступ к родительской сущности (задаче или комментарию)
    parent_task_id = attachment.task_id
    parent_comment_id = attachment.comment_id
    parent_task = None

    if parent_task_id:
        parent_task = crud_task.get(db=db, id=parent_task_id)
    elif parent_comment_id:
        comment = crud_comment.get(db=db, id=parent_comment_id)
        if comment:
            parent_task = crud_task.get(db=db, id=comment.task_id)

    if not parent_task or parent_task.company_id != company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к этому вложению запрещен")
    # TODO: Более гранулярная проверка прав (может ли пользователь видеть эту задачу/комментарий?)
    
    file_path = attachment.file_path
    if not os.path.exists(file_path):
        logger.error(f"Attachment file not found on disk: {file_path} (Attachment ID: {attachment_id})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл вложения не найден на сервере")

    return FileResponse(
        path=file_path, 
        filename=attachment.filename, 
        media_type=attachment.content_type
    )

@attachments_router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    *,
    db: Session = Depends(get_db),
    attachment_id: int = RoutePath(..., description="ID вложения для удаления"),
    current_user_id: int = Depends(deps.get_current_user_id),
    company_id: int = Depends(deps.get_current_company_id),
    current_role: str = Depends(deps.get_current_user_role),
) -> None:
    """Удаляет вложение (автор или админ/менеджер)."""
    attachment = crud_attachment.get(db=db, id=attachment_id)
    if not attachment:
        return None # Идемпотентность

    # Проверяем права на удаление
    is_uploader = attachment.uploader_user_id == current_user_id
    is_manager_or_admin = current_role in [deps.MembershipRole.MANAGER, deps.MembershipRole.ADMIN]
    can_delete = is_uploader or is_manager_or_admin

    if not can_delete:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление этого вложения")
         
    # Проверяем доступ к родительской сущности
    parent_task_id = attachment.task_id
    parent_comment_id = attachment.comment_id
    parent_task = None

    if parent_task_id:
        parent_task = crud_task.get(db=db, id=parent_task_id)
    elif parent_comment_id:
        comment = crud_comment.get(db=db, id=parent_comment_id)
        if comment:
            parent_task = crud_task.get(db=db, id=comment.task_id)

    if not parent_task or parent_task.company_id != company_id:
         # Если вложение принадлежит сущности из другой компании, запрещаем удаление даже админу
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ к родительской сущности вложения запрещен")

    # Удаляем через CRUD (он удалит и файл)
    deleted_attachment = crud_attachment.remove(db=db, id=attachment_id)
    if not deleted_attachment:
        # Эта ситуация не должна произойти, если get выше вернул объект, но для полноты
        logger.warning(f"Attachment {attachment_id} was found but failed to be removed.")
        # Можно вернуть 500 или 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ошибка при удалении вложения")

    return None 