from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_active_superuser
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User, AccessLevel, UserAccessLevel
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserWithAccessLevels,
    AccessLevel as AccessLevelSchema
)


router = APIRouter()

router.post('/', response_model=UserSchema)
def create_user(
        *,
        db: Session = Depends(get_db),
        user_in: UserCreate,
) -> Any:
    '''
    Создание нового пользователя
    '''
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail='Пользователь с таким email уже сущевствует'
        )
    
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        name=user_in.name,
        company_id=user_in.company_id,
        access_level=user_in.access_level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.get('/', response_model=List[UserWithAccessLevels])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    '''
    Возвращает пользователей
    '''
    query = db.query(User).filter(User.deleted_at.is_(None))

    if company_id is not None:
        query = query.filter(User.company_id == company_id)

    users = query.offset(skip).limit(limit).all()
    
    result =[]
    for user in users:
        user_dict = UserSchema.from_orm(user).dict()

        access_levels = []
        user_access_levels = (
            db.query(UserAccessLevel)
            .filter(UserAccessLevel.user_id == user.id)
            .all()
        )

        for ual in user_access_levels:
            access_level = (
                db.query(AccessLevel)
                .filter(AccessLevel.id == ual.access_level_id)
                .first()
            )
            if access_level:
                access_levels.append(access_level.name)

        user_dict['access_levels'] = access_level
        result.append(UserWithAccessLevels(**user_dict))

    return result

@router.get('/{user_id}', response_model=UserWithAccessLevels)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
) -> Any:
    '''
    Получить конкретного пользователя по ID
    '''
    if current_user.id != user_id and current_user.access_level != 'admin':
        raise HTTPException(
            status_code=403,
            detail='Нет прав для авторизации пользователя'
        )
    
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail='Пользователь не найден'
        )
    
    access_levels = []
    user_access_levels = (
        db.query(UserAccessLevel)
        .filter(UserAccessLevel.user_id == user.id)
        .all()
    )

    for ual in user_access_levels:
        access_level = (
            db.query(AccessLevel)
            .filter(AccessLevel.id == ual.access_level_id)
            .first()
        )
        if access_level:
            access_levels.append(access_level.name)

    user_dict = UserSchema.from_orm(user).dict()
    user_dict['access_levels'] = access_levels

    return UserWithAccessLevels(**user_dict)

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Обновляет данные о пользователе
    """
    if current_user.id != user_id and current_user.access_level != "admin":
        raise HTTPException(
            status_code=403,
            detail="Нет прав для обнолвении данных о пользователе",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    update_data = user_in.dict(exclude_unset=True)
    
    if "access_level" in update_data and current_user.access_level != "admin":
        raise HTTPException(
            status_code=403,
            detail="Нет прав для изменения уровня доступа",
        )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Удаление пользователя
    """
    if current_user.id != user_id and current_user.access_level != "admin":
        raise HTTPException(
            status_code=403,
            detail="Нет прав для удаления пользователя",
        )
    
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найлен",
        )
    
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    
    db.add(user)
    db.commit()
    
    return {"detail": "Пользователь удален"}

@router.post("/{user_id}/restore")
def restore_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Восстановление удаленного аккаунта
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.isnot(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Удаленный аккаунт не найден",
        )
    
    user.deleted_at = None
    user.is_active = True
    
    db.add(user)
    db.commit()
    
    return {"detail": "Аккаунт был успешно восстановлен"}

@router.get("/access-levels/", response_model=List[AccessLevelSchema])
def read_access_levels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Восстанавливает все уровни доступа
    """
    access_levels = db.query(AccessLevel).all()
    return access_levels

@router.post("/access-levels/", response_model=AccessLevelSchema)
def create_access_level(
    *,
    db: Session = Depends(get_db),
    access_level_in: AccessLevelSchema,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Создание нового уровня доступа
    """
    existing = db.query(AccessLevel).filter(
        AccessLevel.name == access_level_in.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Уровень доступа с таким названием уже сущевствует",
        )
    
    access_level = AccessLevel(
        name=access_level_in.name,
        description=access_level_in.description,
        permissions=access_level_in.permissions,
    )
    
    db.add(access_level)
    db.commit()
    db.refresh(access_level)
    
    return access_level

@router.post("/{user_id}/access-levels/{access_level_id}")
def assign_access_level(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    access_level_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Назначить уровень доступа пользователю
    """
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден",
        )
    
    access_level = db.query(AccessLevel).filter(
        AccessLevel.id == access_level_id
    ).first()
    
    if not access_level:
        raise HTTPException(
            status_code=404,
            detail="Уровень доступа не найден",
        )
    
    existing = db.query(UserAccessLevel).filter(
        UserAccessLevel.user_id == user_id,
        UserAccessLevel.access_level_id == access_level_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Этот уровень доступа уже есть у пользователя",
        )
    
    user_access_level = UserAccessLevel(
        user_id=user_id,
        access_level_id=access_level_id,
    )
    
    db.add(user_access_level)
    db.commit()
    
    return {"detail": "Добавление нового уровня доступа произошло успешно"}

@router.delete("/{user_id}/access-levels/{access_level_id}")
def remove_access_level(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., gt=0),
    access_level_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Удаляет все уровни доступа
    """
    user_access_level = db.query(UserAccessLevel).filter(
        UserAccessLevel.user_id == user_id,
        UserAccessLevel.access_level_id == access_level_id
    ).first()
    
    if not user_access_level:
        raise HTTPException(
            status_code=404,
            detail="Данного уровня доступа нет у пользователя",
        )
    
    db.delete(user_access_level)
    db.commit()
    
    return {"detail": "Уровень доступа успешно удален"}