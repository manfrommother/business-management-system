from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.db.crud import (
    get_user_by_email, create_user, get_active_user_by_email, get_user_by_id,
    create_verification_token, get_verification_token, delete_verification_token,
    verify_user_email
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.core.security import create_access_token, verify_password, get_password_hash
from app.config import settings
from app.services.email import send_email_verification, send_password_reset
from app.services.messaging import rabbitmq_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегистрирован"
        )
    
    # Создание нового пользователя
    user = create_user(db, user_in)
    
    # Создание токена верификации email
    token_obj = create_verification_token(
        db,
        user.id,
        "email_verification",
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )
    
    # Отправка письма с подтверждением в фоновом режиме
    background_tasks.add_task(
        send_email_verification,
        user.email,
        token_obj.token
    )
    
    # Публикация события создания пользователя
    background_tasks.add_task(
        rabbitmq_service.publish_user_created,
        str(user.id),
        user.email,
        user.name
    )
    
    return user


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Авторизация и получение токена доступа"""
    user = get_active_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создание токена доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Подтверждение email пользователя по токену"""
    token_obj = get_verification_token(db, token)
    if not token_obj or token_obj.type != "email_verification" or token_obj.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен"
        )
    
    # Подтверждение email пользователя
    user = verify_user_email(db, token_obj.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Удаление токена
    delete_verification_token(db, token_obj.id)
    
    return {"message": "Email успешно подтвержден"}


@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Запрос сброса пароля"""
    user = get_active_user_by_email(db, email=email)
    if not user:
        # Не раскрываем информацию о существовании пользователя
        return {"message": "Если ваш email зарегистрирован, вы получите ссылку для сброса пароля"}
    
    # Создание токена сброса пароля
    token_obj = create_verification_token(
        db,
        user.id,
        "password_reset",
        settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )
    
    # Отправка email для сброса пароля в фоновом режиме
    background_tasks.add_task(
        send_password_reset,
        user.email,
        token_obj.token
    )
    
    return {"message": "Если ваш email зарегистрирован, вы получите ссылку для сброса пароля"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Сброс пароля по токену"""
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароль должен содержать не менее 8 символов"
        )
    
    token_obj = get_verification_token(db, token)
    if not token_obj or token_obj.type != "password_reset" or token_obj.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший токен"
        )
    
    # Получение пользователя
    user = get_user_by_id(db, token_obj.user_id)
    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Обновление пароля
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    # Удаление токена
    delete_verification_token(db, token_obj.id)
    
    return {"message": "Пароль успешно сброшен"}