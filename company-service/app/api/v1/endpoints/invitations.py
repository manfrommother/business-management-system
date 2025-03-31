# company-service/app/api/v1/endpoints/invitations.py

from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Позже добавим зависимости
from app.db.session import get_db
# Импортируем CRUD членства для создания пользователя при принятии
from app.crud.crud_membership import crud_membership

router = APIRouter()

# Вспомогательная функция для получения валидного приглашения по коду
async def get_valid_invitation_or_404(
    code: str = Path(..., description="Уникальный код приглашения"),
    db: Session = Depends(get_db)
) -> models.Invitation:
    invitation = crud.crud_invitation.get_by_code(db=db, code=code)
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
    # Можно добавить проверку, что текущий пользователь (если аутентифицирован)
    # соответствует email в приглашении, если он указан
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
        404: {"description": "Приглашение не найдено"},
        400: {"description": "Приглашение недействительно или ошибка при создании пользователя"},
        409: {"description": "Пользователь уже является участником этой компании"}
    }
)
async def accept_invitation(
    *,
    db: Session = Depends(get_db),
    invitation: models.Invitation = Depends(get_valid_invitation_or_404),
    # current_user: models.User = Depends(deps.get_current_active_user) # Нужен текущий пользователь!
    # Замените на реальную зависимость получения текущего пользователя
    current_user_id: int = 1 # ЗАГЛУШКА - ID текущего пользователя
) -> Any:
    """
    Принимает приглашение для текущего аутентифицированного пользователя.
    Создает запись Membership и обновляет статус приглашения.
    """
    # ЗАГЛУШКА: Получаем ID текущего пользователя
    user_id = current_user_id # Заменить на current_user.id

    # Проверяем, не является ли пользователь уже членом этой компании
    existing_membership = crud.crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=invitation.company_id
    )
    if existing_membership and existing_membership.status == models.MembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже являетесь участником этой компании"
        )

    # Если есть неактивное членство - можно реактивировать? Или обновить? Пока создаем новое.
    # TODO: Возможно, стоит обновить существующее неактивное членство вместо создания нового.

    # Создаем членство
    try:
        membership_in = schemas.MembershipCreate(
            user_id=user_id,
            role=invitation.role, # Берем роль из приглашения
            status=models.MembershipStatus.ACTIVE # Сразу активен
            # department_id можно будет назначить позже
        )
        new_membership = crud.crud_membership.create(
            db=db, obj_in=membership_in, company_id=invitation.company_id
        )
    except Exception as e: # Обработка возможных ошибок БД (например, нарушение unique constraint)
        db.rollback()
        # TODO: Логирование ошибки e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось создать членство в компании."
        )

    # Обновляем приглашение (статус + счетчик)
    crud.crud_invitation.increment_usage(db=db, db_obj=invitation)
    # Обновляем статус только если лимит использований не превышен (на случай гонки запросов)
    if invitation.usage_limit is None or invitation.times_used < invitation.usage_limit:
         # Если лимита нет или он еще не достигнут после инкремента
         if invitation.usage_limit is not None and invitation.times_used >= invitation.usage_limit:
              # Если этот инкремент достиг лимита
              crud.crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED) # Или EXPIRED?
         elif invitation.usage_limit is None:
              # Если лимита нет (персональное приглашение)
               crud.crud_invitation.update_status(db=db, db_obj=invitation, status=models.InvitationStatus.ACCEPTED)
    # Если лимит был и он превышен - статус не меняем (он мог уже стать EXPIRED другим потоком)


    return new_membership 