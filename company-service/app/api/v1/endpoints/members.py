# company-service/app/api/v1/endpoints/members.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Импортируем зависимости
from app.db.session import get_db
# Убираем get_company_or_404
# from .departments import get_company_or_404
# Импортируем CRUD напрямую
from app.crud import crud_membership
from app.models.membership import MembershipRole, MembershipStatus # Импортируем MembershipRole и Status

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Membership],
    summary="Получить список участников компании",
    description="Возвращает список пользователей, являющихся участниками компании.",
    responses={403: {"description": "Доступ запрещен"}},
)
async def read_company_members(
    *,
    # company_id из Path будет передан в get_current_member
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_member), # Проверяет членство
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description="Включить неактивных участников в список"),
) -> Any:
    """Получить список участников компании (доступно участникам)."""
    # Права проверены
    members = crud_membership.get_multi_by_company(
        db=db, company_id=membership.company_id, skip=skip, limit=limit, include_inactive=include_inactive
    )
    # TODO: Обогатить данные информацией о пользователе из User Service?
    return members

@router.get(
    "/{user_id}",
    response_model=schemas.Membership,
    summary="Получить информацию об участии пользователя в компании",
    responses={
        404: {"description": "Участник не найден в данной компании"},
        403: {"description": "Доступ запрещен"}
    },
)
async def read_company_member(
    *,
    # company_id из Path будет передан в get_current_member
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    db: Session = Depends(get_db),
    requesting_membership: models.Membership = Depends(deps.get_current_member), # Проверяем членство запрашивающего
) -> Any:
    """Получить информацию о членстве конкретного пользователя в компании (доступно участникам)."""
    # Права проверены
    member = crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=requesting_membership.company_id
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")
    # TODO: Обогатить данные?
    return member

@router.put(
    "/{user_id}",
    response_model=schemas.Membership,
    summary="Обновить данные участника компании",
    responses={
        404: {"description": "Участник не найден в данной компании"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
async def update_company_member(
    *,
    # company_id из Path будет передан в get_current_company_admin
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    db: Session = Depends(get_db),
    member_in: schemas.MembershipUpdate,
    requesting_membership: models.Membership = Depends(deps.get_current_company_admin), # Требуем админа
) -> Any:
    """
    Обновить данные участника компании (роль, отдел, статус). Доступно админам.
    - **department_id**: Новый ID отдела (null для удаления из отдела).
    - **role**: Новая роль (admin, manager, employee).
    - **status**: Новый статус (active, inactive).
    """
    # Права проверены
    member_to_update = crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=requesting_membership.company_id
    )
    if not member_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")

    # TODO: Дополнительные проверки (существование отдела, права на смену роли и т.д.)
    updated_member = crud_membership.update(db=db, db_obj=member_to_update, obj_in=member_in)
    return updated_member

@router.delete(
    "/{user_id}",
    response_model=schemas.Membership,
    summary="Деактивировать участника компании",
     responses={
        404: {"description": "Участник не найден в данной компании"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
async def deactivate_company_member(
    *,
    # company_id из Path будет передан в get_current_company_admin
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    db: Session = Depends(get_db),
    requesting_membership: models.Membership = Depends(deps.get_current_company_admin), # Требуем админа
) -> Any:
    """
    Деактивировать участника (мягкое удаление). Доступно админам.
    Устанавливает статус членства в 'inactive'.
    Запрещено деактивировать себя и последнего активного администратора.
    """
    # Права админа проверены зависимостью
    company_id = requesting_membership.company_id

    # Запрет деактивации самого себя
    if user_id == requesting_membership.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нельзя деактивировать самого себя")

    # Получаем членство пользователя, которого хотим деактивировать
    member_to_deactivate = crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=company_id
    )
    if not member_to_deactivate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")

    # Проверка, является ли пользователь последним активным администратором
    if member_to_deactivate.role == MembershipRole.ADMIN and member_to_deactivate.status == MembershipStatus.ACTIVE:
        active_admins = crud_membership.get_multi_by_company(
            db=db,
            company_id=company_id,
            role=MembershipRole.ADMIN,
            status=MembershipStatus.ACTIVE
        )
        if len(active_admins) <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя деактивировать последнего активного администратора компании."
            )

    deactivated_member = crud_membership.remove_by_user_and_company(
        db=db, user_id=user_id, company_id=company_id
    )
    # Проверка на случай, если remove_by_user_and_company вернул None (хотя мы уже проверили выше)
    if not deactivated_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не удалось деактивировать участника")

    return deactivated_member

# Примечание: Эндпоинт для добавления пользователя (POST /) здесь не реализуем,
# т.к. основной механизм - через приглашения (Invitation).
# Если прямой механизм добавления нужен, его можно добавить по аналогии с create_department. 