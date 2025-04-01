from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=schemas.UserSetting)
async def read_settings(
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Retrieve settings for the current user. Creates default settings if they don't exist."""
    settings = await crud.user_setting.get_or_create(db=db, user_id=current_user_id)
    return settings


@router.put("/", response_model=schemas.UserSetting)
async def update_settings(
    *,
    db: AsyncSession = Depends(deps.get_db),
    settings_in: schemas.UserSettingUpdate,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Update settings for the current user."""
    # Получаем текущие настройки (или создаем, если их нет)
    current_settings = await crud.user_setting.get_or_create(db=db, user_id=current_user_id)

    # Обновляем
    updated_settings = await crud.user_setting.update(
        db=db, db_obj=current_settings, obj_in=settings_in
    )
    return updated_settings 