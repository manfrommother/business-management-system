from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import uuid
from typing import Callable, Optional

from app.db.session import get_db
from app.config import settings
from app.schemas.token import TokenPayload
from app.db.crud import get_member_by_user_and_team
from app.db.models import MemberRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    """Получение ID текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодирование JWT токена
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenPayload(sub=user_id)
        return uuid.UUID(token_data.sub)
    except (JWTError, ValueError):
        raise credentials_exception


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    """Получение информации о текущем пользователе из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодирование JWT токена
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Для упрощения, возвращаем простую структуру с ID пользователя
        # В реальной системе здесь можно было бы выполнить запрос к User Service
        from pydantic import BaseModel
        
        class User(BaseModel):
            id: uuid.UUID
            email: Optional[str] = None
        
        return User(id=uuid.UUID(user_id))
    except (JWTError, ValueError):
        raise credentials_exception


def get_team_member(team_id: uuid.UUID):
    """Фабрика зависимостей для проверки членства пользователя в команде"""
    
    async def _get_team_member(
        current_user_id: uuid.UUID = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ) -> uuid.UUID:
        member = get_member_by_user_and_team(db, current_user_id, team_id)
        if not member or not member.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен: пользователь не является участником команды"
            )
        return current_user_id
    
    return _get_team_member


def check_team_admin(team_id: uuid.UUID):
    """Фабрика зависимостей для проверки, является ли пользователь администратором команды"""
    
    async def _check_team_admin(
        current_user_id: uuid.UUID = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ) -> uuid.UUID:
        member = get_member_by_user_and_team(db, current_user_id, team_id)
        if not member or not member.is_active or member.role != MemberRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен: пользователь не является администратором команды"
            )
        return current_user_id
    
    return _check_team_admin


def check_team_manager(team_id: uuid.UUID):
    """Фабрика зависимостей для проверки, является ли пользователь менеджером или администратором команды"""
    
    async def _check_team_manager(
        current_user_id: uuid.UUID = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ) -> uuid.UUID:
        member = get_member_by_user_and_team(db, current_user_id, team_id)
        if not member or not member.is_active or member.role not in [MemberRole.ADMIN, MemberRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен: пользователь не имеет необходимых прав"
            )
        return current_user_id
    
    return _check_team_manager