# company-service/app/api/v1/endpoints/companies.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps
from app.db.session import get_db
from app.crud import crud_company, crud_membership, crud_invitation, crud_news

router = APIRouter()

# Эндпоинт для получения списка компаний
@router.get(
    "/",
    response_model=List[schemas.CompanyInList],
    summary="Получить список компаний",
    description="Возвращает список компаний с пагинацией (требуется аутентификация).",
)
def read_companies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(deps.get_current_user_id)
) -> Any:
    """
    Получить список компаний (доступно всем аутентифицированным пользователям).
    """
    companies = crud_company.get_multi(db, skip=skip, limit=limit)
    return companies

# Эндпоинт для создания новой компании
@router.post(
    "/",
    response_model=schemas.Company,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую компанию",
    description="Регистрирует новую компанию в системе.",
)
def create_company(
    *,
    db: Session = Depends(get_db),
    company_in: schemas.CompanyCreate,
    current_user_id: int = Depends(deps.get_current_user_id),
) -> Any:
    """
    Создать новую компанию.
    - **name**: Название компании (обязательно)
    - **description**: Описание (опционально)
    ... другие поля из CompanyCreate
    """
    company = crud_company.create(db=db, obj_in=company_in)
    return company

# Эндпоинт для получения информации о конкретной компании
@router.get(
    "/{company_id}",
    response_model=schemas.Company,
    summary="Получить информацию о компании",
    description="Возвращает детальную информацию о компании по её ID.",
    responses={
        404: {"description": "Компания не найдена"},
        403: {"description": "Доступ запрещен"}
    },
)
def read_company(
    *,
    company_id: int = Path(..., description="ID компании"),
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_member)
) -> Any:
    """
    Получить информацию о компании по ID.
    Доступно только активным участникам компании.
    """
    company = crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return company

# Эндпоинт для обновления информации о компании
@router.put(
    "/{company_id}",
    response_model=schemas.Company,
    summary="Обновить информацию о компании",
    description="Обновляет данные компании по её ID.",
     responses={
        404: {"description": "Компания не найдена"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
def update_company(
    *,
    company_id: int = Path(..., description="ID компании"),
    db: Session = Depends(get_db),
    company_in: schemas.CompanyUpdate,
    membership: models.Membership = Depends(deps.get_current_company_admin)
) -> Any:
    """
    Обновить информацию о компании.
    Доступно только администраторам компании.
    """
    company = crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена",
        )
    if company.id != membership.company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка доступа")

    company = crud_company.update(db=db, db_obj=company, obj_in=company_in)
    return company

# Эндпоинт для мягкого удаления компании
@router.delete(
    "/{company_id}",
    response_model=schemas.Company,
    summary="Мягкое удаление компании",
    description="Деактивирует компанию (мягкое удаление).",
     responses={
        404: {"description": "Компания не найдена"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
def delete_company(
    *,
    company_id: int = Path(..., description="ID компании"),
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_company_admin)
) -> Any:
    """
    Мягкое удаление компании (деактивация).
    Доступно только администраторам компании.
    """
    company = crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена",
        )
    if company.id != membership.company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка доступа")

    deleted_company = crud_company.remove(db=db, id=company_id)
    if not deleted_company:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не удалось удалить компанию")
    return deleted_company

# Эндпоинт для восстановления компании
@router.post(
    "/{company_id}/restore",
    response_model=schemas.Company,
    summary="Восстановить компанию",
    description="Восстанавливает компанию после мягкого удаления.",
    responses={
        404: {"description": "Удаленная компания не найдена"},
        403: {"description": "Доступ запрещен"}
    },
)
def restore_company(
    *,
    company_id: int = Path(..., description="ID компании"),
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_company_admin)
) -> Any:
    """
    Восстановить мягко удаленную компанию.
    Доступно администраторам компании (TODO: или только суперадмину?).
    """
    if company_id != membership.company_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ошибка доступа")

    restored_company = crud_company.restore(db=db, id=company_id)
    if not restored_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена или не была удалена",
        )
    return restored_company

# --- Эндпоинты для Приглашений --- #

@router.post(
    "/{company_id}/invitations",
    response_model=schemas.Invitation,
    status_code=status.HTTP_201_CREATED,
    summary="Создать приглашение в компанию",
    description="Генерирует уникальный код или ссылку для приглашения пользователей.",
    responses={403: {"description": "Доступ запрещен (требуется админ)"}},
)
def create_invitation(
    *,
    db: Session = Depends(get_db),
    invitation_in: schemas.InvitationCreate,
    membership: models.Membership = Depends(deps.get_current_company_admin)
) -> Any:
    """
    Создать новое приглашение. Доступно администраторам компании.
    - **email**: Email приглашаемого (опционально, для персональных).
    - **role**: Роль назначаемая при принятии (по умолчанию 'employee').
    - **expires_at**: Срок действия (UTC, опционально, по умолчанию 7 дней).
    - **usage_limit**: Лимит использований (опционально, null/0 - безлимит).
    """
    current_user_id = membership.user_id

    if invitation_in.usage_limit is None:
        if invitation_in.email:
            invitation_in.usage_limit = 1

    invitation = crud_invitation.create_with_company(
        db=db,
        obj_in=invitation_in,
        company_id=membership.company_id,
        created_by_user_id=current_user_id
    )
    return invitation

# --- Эндпоинты для Статистики --- #

@router.get(
    "/{company_id}/stats",
    response_model=schemas.CompanyStats,
    summary="Получить статистику по компании",
    description="Возвращает основные статистические показатели для компании.",
    responses={403: {"description": "Доступ запрещен (требуется админ)"}},
)
def get_company_stats(
    *,
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_company_admin)
) -> Any:
    """
    Получить статистику компании. Доступно администраторам.
    - Общее количество активных участников.
    - Количество активных приглашений.
    - Количество опубликованных новостей.
    - Распределение активных участников по отделам.
    """
    company_id = membership.company_id

    total_members = crud_membership.count_active_by_company(db=db, company_id=company_id)
    pending_invitations = crud_invitation.count_pending_by_company(db=db, company_id=company_id)
    published_news = crud_news.count_published_by_company(db=db, company_id=company_id)
    member_distribution_raw = crud_membership.get_distribution_by_department(db=db, company_id=company_id)

    department_ids = [dept_id for dept_id in member_distribution_raw.keys() if dept_id != -1]
    departments = {}
    if department_ids:
        department_models = db.query(models.Department).filter(
            models.Department.company_id == company_id,
            models.Department.id.in_(department_ids)
        ).all()
        departments = {dept.id: dept.name for dept in department_models}

    members_by_department_list: List[schemas.DepartmentMemberCount] = []
    for dept_id, count in member_distribution_raw.items():
        dept_name = departments.get(dept_id, "Без отдела")
        members_by_department_list.append(
            schemas.DepartmentMemberCount(
                department_id=dept_id if dept_id != -1 else None,
                department_name=dept_name,
                member_count=count
            )
        )

    return schemas.CompanyStats(
        total_members=total_members,
        pending_invitations=pending_invitations,
        published_news=published_news,
        members_by_department=members_by_department_list
    ) 