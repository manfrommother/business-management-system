# company-service/app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import logging

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли обычный пароль хешированному."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Генерирует хеш пароля."""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Создает JWT токен доступа."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    """
    Декодирует JWT токен и возвращает ID пользователя (sub).
    Возвращает None в случае ошибки декодирования или истечения срока действия.
    """
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        # Проверяем тип sub и возвращаем его как строку
        user_id: Optional[Any] = payload.get("sub")
        if user_id is None:
            # TODO: Логировать ошибку декодирования? - Логируем ниже
            return None
        # Можно добавить проверку на тип user_id, если необходимо
        return str(user_id)
    except jwt.ExpiredSignatureError:
        # Токен истек
        logger.warning("Access token has expired.")
        return None
    except jwt.JWTError as e:
        # Ошибка декодирования
        logger.error(f"Error decoding access token: {e}")
        return None 