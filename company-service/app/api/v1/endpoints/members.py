# company-service/app/api/v1/endpoints/members.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Позже добавим зависимости для проверки прав
from app.db.session import get_db
# Импортируем зависимость для проверки компании
from .departments import get_company_or_404

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Membership],
    summary="Получить список участников компании",
    description="Возвращает список пользователей, являющихся участниками компании.",
    # TODO: Права: участник компании
)
async def read_company_members(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = Query(False, description="Включить неактивных участников в список"),
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить список участников компании."""
    # TODO: Проверка прав
    members = crud.crud_membership.get_multi_by_company(
        db=db, company_id=company.id, skip=skip, limit=limit, include_inactive=include_inactive
    )
    # TODO: Обогатить данные информацией о пользователе из User Service?
    return members

@router.get(
    "/{user_id}",
    response_model=schemas.Membership,
    summary="Получить информацию об участии пользователя в компании",
    responses={404: {"description": "Участник не найден в данной компании"}},
    # TODO: Права: участник компании
)
async def read_company_member(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить информацию о членстве конкретного пользователя в компании."""
    # TODO: Проверка прав
    member = crud.crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=company.id
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")
    # TODO: Обогатить данные?
    return member

@router.put(
    "/{user_id}",
    response_model=schemas.Membership,
    summary="Обновить данные участника компании",
    responses={404: {"description": "Участник не найден в данной компании"}},
    # TODO: Права: администратор компании
)
async def update_company_member(
    *,
    db: Session = Depends(get_db),
    member_in: schemas.MembershipUpdate,
    company: models.Company = Depends(get_company_or_404),
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """
    Обновить данные участника компании (роль, отдел, статус).
    - **department_id**: Новый ID отдела (null для удаления из отдела).
    - **role**: Новая роль (admin, manager, employee).
    - **status**: Новый статус (active, inactive).
    """
    # TODO: Проверка прав
    member = crud.crud_membership.get_by_user_and_company(
        db=db, user_id=user_id, company_id=company.id
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")

    # TODO: Дополнительные проверки:
    # - Существует ли department_id, если указан, и принадлежит ли он этой компании.
    # - Права на изменение роли (например, нельзя понизить единственного админа).
    updated_member = crud.crud_membership.update(db=db, db_obj=member, obj_in=member_in)
    return updated_member

@router.delete(
    "/{user_id}",
    response_model=schemas.Membership, # Возвращаем измененный объект
    summary="Деактивировать участника компании",
    responses={404: {"description": "Участник не найден в данной компании"}},
    # TODO: Права: администратор компании
)
async def deactivate_company_member(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    user_id: int = Path(..., description="ID пользователя (из User Service)"),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """
    Деактивировать участника (мягкое удаление).
    Устанавливает статус членства в 'inactive'.
    """
    # TODO: Проверка прав
    # TODO: Нельзя деактивировать себя? Или последнего админа?
    deactivated_member = crud.crud_membership.remove_by_user_and_company(
        db=db, user_id=user_id, company_id=company.id
    )
    if not deactivated_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник не найден в этой компании")
    return deactivated_member

# Примечание: Эндпоинт для добавления пользователя (POST /) здесь не реализуем,
# т.к. основной механизм - через приглашения (Invitation).
# Если прямой механизм добавления нужен, его можно добавить по аналогии с create_department. 