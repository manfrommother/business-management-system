# task-service/app/api/deps.py
import logging
from typing import Generator, Optional, List

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

# Импортируем модели и CRUD сервиса компаний, если потребуется проверять членство
# from company_service import models as company_models, crud as company_crud
# Или предполагаем, что информация о ролях/компании приходит в токене

from app import schemas # Локальные схемы, если нужны (например, TokenPayload)
from app.core import security
from app.core.config import settings
from app.db.session import get_db

# Если проверка ролей/членства будет через Company Service API, нужны будут HTTP-клиенты (httpx)

logger = logging.getLogger(__name__)

# Путь к эндпоинту для получения токена (предполагаем, что он в User Service)
# Этот путь используется для документации OpenAPI, а не для реальной логики здесь.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token" # Пример! Заменить на реальный путь к User Service login
)

# Предполагаем, что роли определены где-то глобально или передаются как строки
# Можно импортировать Enum из company-service, если он доступен как библиотека
# from company_service.app.models.membership import MembershipRole
class MembershipRole:
    # Заглушка для ролей
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

# Обновляем схему TokenPayload
class TokenPayload(BaseModel):
    sub: Optional[int] = None # user_id
    company_id: Optional[int] = None
    role: Optional[str] = None # Роль пользователя в указанной company_id

def get_token_payload(token: str = Depends(reusable_oauth2)) -> TokenPayload:
    """
    Декодирует и валидирует JWT токен, возвращая payload.
    Вызывает HTTPException 401 при невалидном токене.
    """
    try:
        payload_data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload_data)
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

def get_current_user_id(payload: TokenPayload = Depends(get_token_payload)) -> int:
    """Получает user_id из валидного токена."""
    user_id = payload.sub
    if user_id is None:
        # Эта проверка дублируется валидацией Pydantic, но для надежности оставим
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID (sub) not found in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

def get_current_company_id(payload: TokenPayload = Depends(get_token_payload)) -> int:
    """Получает company_id из валидного токена."""
    company_id = payload.company_id
    if company_id is None:
        logger.warning(f"Company ID not found in token for user {payload.sub}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403, так как пользователь аутентифицирован, но нет контекста компании
            detail="Company context not found in token"
        )
    return company_id

def get_current_user_role(payload: TokenPayload = Depends(get_token_payload)) -> str:
    """Получает роль пользователя из валидного токена."""
    role = payload.role
    if role is None:
        logger.warning(f"Role not found in token for user {payload.sub} in company {payload.company_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role not found in token"
        )
    return role

# Зависимости для проверки прав
def require_role(required_role: str):
    """Фабрика зависимостей для проверки конкретной роли."""
    def dependency(current_role: str = Depends(get_current_user_role)) -> str:
        if current_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role '{required_role}'."
            )
        return current_role
    return dependency

def require_min_role(min_role_level: List[str]):
    """Фабрика зависимостей для проверки минимальной роли (например, менеджер или админ)."""
    def dependency(current_role: str = Depends(get_current_user_role)) -> str:
        if current_role not in min_role_level:
            allowed_roles = ", ".join(min_role_level)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {allowed_roles}."
            )
        return current_role
    return dependency

# Конкретные зависимости проверки прав
require_admin = require_role(MembershipRole.ADMIN)
require_manager = require_role(MembershipRole.MANAGER)
require_employee = require_role(MembershipRole.EMPLOYEE)
require_manager_or_admin = require_min_role([MembershipRole.MANAGER, MembershipRole.ADMIN])

# Пример зависимости, извлекающей ID компании из токена (если он там есть)
# def get_current_company_id(token_data: TokenPayload = Depends(get_token_payload)) -> int:
#     company_id = token_data.company_id
#     if company_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Company ID not found in token"
#         )
#     return company_id

# TODO: Реализовать зависимости для проверки прав (например, is_manager, can_create_task и т.д.)
# Эти зависимости могут:
# 1. Получать роль пользователя из токена.
# 2. Делать запрос к Company Service для получения роли/прав.
# 3. Проверять права на основе полученной роли.

# Пример простой зависимости, которая требует ID пользователя
def get_authenticated_user(user_id: int = Depends(get_current_user_id)) -> int:
    """Простая зависимость, требующая аутентифицированного пользователя."""
    return user_id 