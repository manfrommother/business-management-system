# company-service/app/api/deps.py

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.membership import Membership, MembershipRole
from app.crud.crud_membership import crud_membership
# Импортируем модели для аннотаций типов (если нужно, хотя user здесь нет)
from app import models

# Схема OAuth2 для получения токена из заголовка Authorization: Bearer <token>
# tokenUrl не имеет значения для этого сервиса, т.к. токены выдает User Service
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token") # URL заглушка

def get_current_user_id(
    token: str = Depends(reusable_oauth2)
) -> int:
    """
    Декодирует токен и возвращает ID пользователя (из поля 'sub').
    Вызывает HTTPException 401, если токен невалиден или отсутствует.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise credentials_exception # Если sub не число
    return user_id_int

# --- Зависимости для проверки ролей в компании ---

async def get_membership_or_403(
    *,
    db: Session = Depends(get_db),
    company_id: int = Path(..., description="ID компании из пути"),
    current_user_id: int = Depends(get_current_user_id)
) -> Membership:
    """
    Получает запись о членстве текущего пользователя в указанной компании.
    Вызывает HTTPException 403, если пользователь не является участником.
    """
    membership = crud_membership.get_by_user_and_company(
        db=db, user_id=current_user_id, company_id=company_id
    )
    if not membership or membership.status != models.MembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для доступа к этой компании",
        )
    return membership

def get_current_member(
    membership: Membership = Depends(get_membership_or_403)
) -> Membership:
    """Зависимость: Текущий пользователь является активным участником компании."""
    # Просто возвращаем результат предыдущей зависимости
    return membership

def get_current_company_admin(
    membership: Membership = Depends(get_membership_or_403)
) -> Membership:
    """Зависимость: Текущий пользователь является администратором компании."""
    if membership.role != MembershipRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора компании",
        )
    return membership

def get_current_company_manager(
     membership: Membership = Depends(get_membership_or_403)
) -> Membership:
    """
    Зависимость: Текущий пользователь - админ ИЛИ менеджер компании.
    (Может использоваться для прав на создание/редактирование в рамках компании).
    """
    if membership.role not in [MembershipRole.ADMIN, MembershipRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора или менеджера компании",
        )
    return membership

# TODO: Добавить более гранулярные проверки прав, если необходимо
# Например, проверка, что пользователь является руководителем конкретного отдела
# def get_department_manager(...) -> ...

# Заглушка для суперадмина (если он есть в системе)
# def get_current_superuser(...) -> ... 