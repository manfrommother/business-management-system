# company-service/app/api/v1/endpoints/invitations.py

from typing import Any
from datetime import datetime, timezone
import logging # Добавляем логгер

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Импортируем зависимости
from app.db.session import get_db
# Импортируем CRUD членства и приглашений напрямую
from app.crud import crud_membership, crud_invitation
from app.models.membership import MembershipStatus # Добавляем статус

logger = logging.getLogger(__name__) # Инициализируем логгер

router = APIRouter()

# Вспомогательная функция для получения валидного приглашения по коду
async def get_valid_invitation_or_404( # Эта зависимость не требует аутентификации
    code: str = Path(..., description="Уникальный код приглашения"),
    db: Session = Depends(get_db)
) -> models.Invitation:
    invitation = crud_invitation.get_by_code(db=db, code=code)
    now_aware = datetime.now(timezone.utc)

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Приглашение не найдено")
    if invitation.status != models.InvitationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Приглашение уже использовано или отозвано")
    if invitation.expires_at and invitation.expires_at < now_aware:
        # Автоматически меняем статус на EXPIRED, если просрочено
        crud.crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.EXPIRED)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия приглашения истек")
    if invitation.usage_limit is not None and invitation.times_used >= invitation.usage_limit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Достигнут лимит использования приглашения")

    return invitation

@router.get(
    "/{code}",
    response_model=schemas.Invitation, # Возвращаем инфо о приглашении, но без чувствительных данных
    summary="Проверить действительность приглашения",
    responses={
        404: {"description": "Приглашение не найдено"},
        400: {"description": "Приглашение недействительно (просрочено, использовано, отозвано)"}
    }
)
async def check_invitation(
    *,
    invitation: models.Invitation = Depends(get_valid_invitation_or_404)
    # Не требует аутентификации
) -> Any:
    """
    Проверяет, действителен ли код приглашения.
    Возвращает информацию о приглашении, если оно валидно.
    """
    # Не возвращаем все данные, чтобы не раскрывать лишнего
    return schemas.Invitation.model_validate(invitation)

@router.post(
    "/{code}/accept",
    response_model=schemas.Membership, # Возвращаем созданное членство
    summary="Принять приглашение",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Требуется аутентификация"},
        404: {"description": "Приглашение не найдено"},
        400: {"description": "Приглашение недействительно или ошибка"},
        409: {"description": "Пользователь уже является участником"}
    }
)
async def accept_invitation(
    *,
    db: Session = Depends(get_db),
    invitation: models.Invitation = Depends(get_valid_invitation_or_404),
    current_user_id: int = Depends(deps.get_current_user_id) # Требуем аутентификацию
) -> Any:
    """
    Принимает приглашение для текущего аутентифицированного пользователя.
    Создает запись Membership и обновляет статус приглашения.
    Если пользователь уже активен, возвращает 409.
    Если есть неактивное членство, оно реактивируется.
    """
    user_id = current_user_id
    company_id = invitation.company_id

    # Проверяем, не является ли пользователь уже членом этой компании
    existing_membership = crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=company_id
    )

    if existing_membership:
        if existing_membership.status == MembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Вы уже являетесь активным участником этой компании"
            )
        else: # Если статус INACTIVE
            # Реактивируем существующее членство
            try:
                # Обновляем роль (если в приглашении другая) и статус
                membership_update = schemas.MembershipUpdate(
                    role=invitation.role, # Обновляем роль на ту, что в приглашении
                    status=MembershipStatus.ACTIVE
                )
                reactivated_membership = crud_membership.update(
                    db=db, db_obj=existing_membership, obj_in=membership_update
                )
                # Обновляем приглашение (статус + счетчик)
                crud_invitation.increment_usage(db=db, db_obj=invitation)
                # Логика обновления статуса приглашения (аналогично случаю создания)
                if invitation.usage_limit is None or invitation.times_used < invitation.usage_limit:
                     if invitation.usage_limit is not None and invitation.times_used >= invitation.usage_limit:
                          crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED)
                     elif invitation.usage_limit is None:
                           crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED)

                return reactivated_membership
            except Exception as e:
                db.rollback()
                logger.error(f"Ошибка реактивации членства (user_id={user_id}, company_id={company_id}) при принятии приглашения {invitation.code}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Не удалось реактивировать членство в компании."
                )

    # Если существующего членства нет, создаем новое
    try:
        membership_in = schemas.MembershipCreate(
            user_id=user_id,
            role=invitation.role, # Берем роль из приглашения
            status=MembershipStatus.ACTIVE # Сразу активен
        )
        new_membership = crud_membership.create(
            db=db, obj_in=membership_in, company_id=company_id
        )
        # Обновляем приглашение (статус + счетчик) - вынесено в общий блок ниже
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка создания членства (user_id={user_id}, company_id={company_id}) при принятии приглашения {invitation.code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать членство в компании."
        )

    # Обновляем приглашение (статус + счетчик) - теперь только после успешного создания/реактивации
    crud_invitation.increment_usage(db=db, db_obj=invitation)
    if invitation.usage_limit is None or invitation.times_used < invitation.usage_limit:
         if invitation.usage_limit is not None and invitation.times_used >= invitation.usage_limit:
              crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED)
         elif invitation.usage_limit is None:
               crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED)

    return new_membership # Возвращаем новое или реактивированное членство 