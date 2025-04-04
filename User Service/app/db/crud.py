from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid

from app.db.models import User, VerificationToken
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, generate_verification_token


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    '''Получение пользователя по email'''
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    '''Полоучения пользователя под ID'''
    return db.query(User).filter(User.id == user_id).first()

def get_active_user_by_email(db: Session, email: str) -> Optional[User]:
    '''Получение активного пользователя по email'''
    return db.query(User).filter(
        User.email == email,
        User.is_active == True,
        User.is_deleted == False
    ).first()

def create_user(db: Session, user_create: UserCreate) -> User:
    '''Создание нового пользолвателя'''
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        name=user_create.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[User]:
    '''Обновления данных пользователя'''
    db_user = get_user_by_id(db, user_id)
    if not db_user or db_user.is_deleted:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if 'password' in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop('password'))

    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def mark_user_deleted(db: Session, user_id: uuid.UUID) -> Optional[User]:
    '''Помечает пользователя как удаленного'''
    db_user = get_user_by_id(db, user_id)
    if not db_user or db_user.is_deleted:
        return None
    
    db_user.mark_deleted()
    db.commit()
    db.refresh(db_user)
    return db_user

def restore_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    '''Восстановить удаленного пользователя'''
    db_user = get_user_by_id(db, user_id)
    if not db_user or not db_user.is_deleted:
        return None
    
    if db_user.restore():
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def create_verification_token(db: Session, user_id: uuid.UUID, token_type: str, expires_hours: int) -> VerificationToken:
    '''Создает токена верификации'''
    token = generate_verification_token()
    db_token = VerificationToken(
        user_id=user_id,
        token=token,
        type=token_type,
        expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

def get_verification_token(db: Session, token: str) -> Optional[VerificationToken]:
    '''Получает токен верификации'''
    return db.query(VerificationToken).filter(VerificationToken.token == token).first()

def delete_verification_token(db: Session, token: str) -> None:
    '''Удаляет токен верификации'''
    db.query(VerificationToken).filter(VerificationToken.token == token).delete()
    db.commit()

def permanently_delete_expired_user(db: Session) -> int:
    '''Окончательно удаляет пользователя, помеченных на удаление более 30 дней назад'''
    threshold_date = datetime.utcnow() - timedelta(days=30)
    result =db.query(User).filter(
        User.is_deleted == True,
        User.deletion_date <= threshold_date
    ).delete()
    db.commit()
    return result
