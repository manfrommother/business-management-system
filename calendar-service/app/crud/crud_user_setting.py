from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.user_setting import UserSetting
from app.schemas.user_setting import UserSettingCreate, UserSettingUpdate

# Переопределяем CRUDBase, т.к. PK здесь user_id, а не id
class CRUDUserSetting(CRUDBase[UserSetting, UserSettingCreate, UserSettingUpdate]):

    async def get(self, db: AsyncSession, user_id: int) -> Optional[UserSetting]:
        # Переопределяем get для использования user_id
        result = await db.execute(select(self.model).filter(self.model.user_id == user_id))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserSettingCreate) -> UserSetting:
        # Проверяем, существуют ли уже настройки для этого пользователя
        existing_settings = await self.get(db, user_id=obj_in.user_id)
        if existing_settings:
            # Если существуют, можно либо вернуть ошибку, либо обновить
            # В данном случае, обновим существующие
            return await self.update(db, db_obj=existing_settings, obj_in=obj_in)
        # Если не существуют, создаем новые
        return await super().create(db, obj_in=obj_in)

    async def update(self, db: AsyncSession, *, db_obj: UserSetting, obj_in: UserSettingUpdate) -> UserSetting:
        # Используем стандартный update из CRUDBase
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

    async def get_or_create(self, db: AsyncSession, *, user_id: int) -> UserSetting:
        """Получает настройки или создает их по умолчанию, если они не существуют."""
        settings = await self.get(db, user_id=user_id)
        if not settings:
            settings_in = UserSettingCreate(user_id=user_id)
            settings = await self.create(db, obj_in=settings_in)
        return settings

    # Метод remove не имеет смысла, т.к. у пользователя всегда должны быть настройки
    # Вместо этого можно сбросить к значениям по умолчанию при удалении пользователя (через события)


user_setting = CRUDUserSetting(UserSetting) 