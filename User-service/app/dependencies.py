from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.core.security import oauth2_scheme
from app.schemas.token import TokenPayload
from app.config import settings
from app.db.crud import get_user_by_id

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    """Получение текущего пользователя по JWT токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невозможно проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenPayload(sub=user_id)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(db, uuid.UUID(token_data.sub))
    if user is None:
        raise credentials_exception
    
    if user.is_deleted or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неактивный пользователь")
    
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Получение активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user

async def get_current_admin(current_user = Depends(get_current_user)):
    """Проверка, является ли текущий пользователь администратором"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return current_user