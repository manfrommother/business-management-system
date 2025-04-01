from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.session import AsyncSessionLocal
from app.core.security import decode_access_token
from app.core.config import settings
# from app.models.user import User # Модель User здесь не нужна, т.к. берем ID из токена
# import app.crud as crud # CRUD User здесь не нужен

# Указываем URL для получения токена (может быть в другом сервисе)
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: str = Depends(reusable_oauth2)
) -> int: # Возвращаем просто ID пользователя
    """Извлекает ID пользователя из JWT токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    # В реальном приложении здесь может быть проверка, активен ли пользователь,
    # или получение дополнительных данных о пользователе из User Service.
    # user = await crud.user.get(db, id=user_id)
    # if not user or not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return int(user_id) # Убедимся, что возвращаем int

# Заглушка get_current_user_stub больше не нужна, можно удалить или оставить для тестов
async def get_current_user_stub() -> int:
    return 1 # Возвращаем ID=1 для примера 