from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash
)
from app.db.session import get_db
from app.models.user import User, Session as UserSession, AccountRecovery
from app.schemas.user import (
    Token,
    User as UserSchema,
    RefreshToken,
    RequestPasswordReset,
    PasswordReset,
    RequestAccountRecovery,
    CompleteAccountRecovery
)

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аккаунт не активирован",
        )
    
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аккаунт был удален",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token()

    expires_at = datetime.utcnow() + access_token_expires
    refresh_expires_at = datetime.utcnow() + refresh_token_expires
    
    session = UserSession(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@router.post("/refresh", response_model=Token)
def refresh_token(
    request: Request,
    refresh_token_in: RefreshToken = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    session = db.query(UserSession).filter(
        UserSession.refresh_token == refresh_token_in.refresh_token
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )
    
    if datetime.utcnow() >= session.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
        )
    
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт не активирован или удален",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.utcnow() + access_token_expires
    
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # Update session
    session.token = access_token
    session.expires_at = expires_at
    session.ip_address = request.client.host if request.client else None
    session.user_agent = request.headers.get("User-Agent")
    
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": session.refresh_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }

@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные для авторизации",
        )
    
    token = auth_header.split(" ")[1]
    
    session = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.token == token
    ).first()
    
    if session:
        db.delete(session)
        db.commit()
    
    return {"detail": "Successfully logged out"}

@router.post("/password-reset/request")
def request_password_reset(
    reset_request: RequestPasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user or not user.is_active or user.deleted_at is not None:
        return {"detail": "Ссылка для сброса пароля была отправлена на email"}

    reset_token = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(hours=settings.ACCOUNT_RECOVERY_EXPIRE_HOURS)
    
    recovery = AccountRecovery(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
        used=False
    )
    
    db.add(recovery)
    db.commit()
    
    
    return {"detail": "Ссылка для сброса пароля была отправлена на email"}

@router.post("/password-reset/complete")
def complete_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
) -> Any:
    recovery = db.query(AccountRecovery).filter(
        AccountRecovery.token == reset_data.token,
        AccountRecovery.used == False
    ).first()
    
    if not recovery or datetime.utcnow() >= recovery.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен",
        )
    
    user = db.query(User).filter(User.id == recovery.user_id).first()
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не активирован или удален",
        )
    
    user.password_hash = get_password_hash(reset_data.new_password)
    
    recovery.used = True
    
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    
    db.add(user)
    db.add(recovery)
    db.commit()
    
    return {"detail": "Пароль был успешно изменен"}

@router.post("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user
    """
    return current_user

@router.post("/recover-account/request")
def request_account_recovery(
    recovery_request: RequestAccountRecovery,
    db: Session = Depends(get_db)
) -> Any:

    user = db.query(User).filter(
        User.email == recovery_request.email,
        User.deleted_at.isnot(None)
    ).first()
    
    if not user:
        return {"detail": "Ссылка для сброса пароля была отправлена на email"}
    
    recovery_token = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(hours=settings.ACCOUNT_RECOVERY_EXPIRE_HOURS)
    
    recovery = AccountRecovery(
        user_id=user.id,
        token=recovery_token,
        expires_at=expires_at,
        used=False
    )
    
    db.add(recovery)
    db.commit()
    
    return {"detail": "Ссылка для сброса пароля была отправлена на email"}

@router.post("/recover-account/complete")
def complete_account_recovery(
    recovery_data: CompleteAccountRecovery,
    db: Session = Depends(get_db)
) -> Any:
    recovery = db.query(AccountRecovery).filter(
        AccountRecovery.token == recovery_data.token,
        AccountRecovery.used == False
    ).first()
    
    if not recovery or datetime.utcnow() >= recovery.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный токен",
        )
    
    user = db.query(User).filter(User.id == recovery.user_id).first()
    if not user or user.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить аккаунт",
        )
    
    user.deleted_at = None
    user.is_active = True
    
    recovery.used = True
    
    db.add(user)
    db.add(recovery)
    db.commit()
    
    return {"detail": "Удаление аккаунта прошло успешно!"}