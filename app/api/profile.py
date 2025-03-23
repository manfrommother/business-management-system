from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.db.crud import update_user, mark_user_deleted, restore_user
from app.schemas.user import UserUpdate, UserResponse
from app.dependencies import get_current_user
from app.db.models import User
from app.services.messaging import rabbitmq_service
from app.services.redis import redis_service
from app.services.email import send_account_deletion_notification
from app.config import settings

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Получение профиля текущего пользователя"""
    # Сначала пробуем получить из кэша
    cached_profile = await redis_service.get_cached_user_profile(str(current_user.id))
    if cached_profile:
        return cached_profile
    
    # Кэшируем профиль для будущих запросов
    user_data = UserResponse.from_orm(current_user).dict()
    await redis_service.cache_user_profile(str(current_user.id), user_data)
    
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление профиля пользователя"""
    updated_user = update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Инвалидация кэша
    background_tasks.add_task(
        redis_service.invalidate_user_cache,
        str(current_user.id)
    )
    
    # Публикация события обновления пользователя
    background_tasks.add_task(
        rabbitmq_service.publish_user_updated,
        str(current_user.id),
        user_update.dict(exclude_unset=True)
    )
    
    return updated_user


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отметить пользователя как удаленного"""
    deleted_user = mark_user_deleted(db, current_user.id)
    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Инвалидация кэша
    background_tasks.add_task(
        redis_service.invalidate_user_cache,
        str(current_user.id)
    )
    
    # Публикация события удаления пользователя
    background_tasks.add_task(
        rabbitmq_service.publish_user_deleted,
        str(current_user.id)
    )
    
    # Отправка уведомления об удалении
    background_tasks.add_task(
        send_account_deletion_notification,
        current_user.email,
        settings.ACCOUNT_DELETION_DAYS
    )
    
    return None


@router.post("/restore", response_model=UserResponse)
async def restore_profile(
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Восстановление удаленного пользователя"""
    restored_user = restore_user(db, user_id)
    if not restored_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден или не может быть восстановлен"
        )
    
    # Публикация события восстановления пользователя
    background_tasks.add_task(
        rabbitmq_service.publish_user_restored,
        str(restored_user.id)
    )
    
    return restored_user