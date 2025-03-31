# company-service/app/api/v1/endpoints/companies.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas, crud, models # Импортируем все сразу для удобства
from app.api import deps # Позже создадим файл с зависимостями (например, get_current_user)
from app.db.session import get_db # Импортируем зависимость для сессии БД

router = APIRouter()

# Эндпоинт для получения списка компаний
@router.get(
    "/",
    response_model=List[schemas.CompanyInList],
    summary="Получить список компаний",
    description="Возвращает список компаний с пагинацией.",
    # TODO: Добавить зависимости для прав доступа (например, только для аутентифицированных)
)
def read_companies(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(deps.get_current_active_user) # Пример зависимости прав
) -> Any:
    """
    Получить список компаний.
    Пока доступно всем, в будущем ограничить права.
    """
    companies = crud.crud_company.get_multi(db, skip=skip, limit=limit)
    return companies

# Эндпоинт для создания новой компании
@router.post(
    "/",
    response_model=schemas.Company,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую компанию",
    description="Регистрирует новую компанию в системе.",
    # TODO: Добавить зависимости для прав доступа (например, только суперадмин или спец. роль)
)
def create_company(
    *,
    db: Session = Depends(get_db),
    company_in: schemas.CompanyCreate,
    # current_user: models.User = Depends(deps.get_current_active_user) # Пример
) -> Any:
    """
    Создать новую компанию.
    - **name**: Название компании (обязательно)
    - **description**: Описание (опционально)
    ... другие поля из CompanyCreate
    """
    # TODO: Проверить, не существует ли уже компания с таким именем?
    # company = crud.crud_company.get_by_name(db, name=company_in.name)
    # if company:
    #     raise HTTPException(...)
    company = crud.crud_company.create(db=db, obj_in=company_in)
    # TODO: Возможно, создать первого пользователя-администратора для компании?
    # Или связать с создавшим пользователем (current_user.id)
    return company

# Эндпоинт для получения информации о конкретной компании
@router.get(
    "/{company_id}",
    response_model=schemas.Company,
    summary="Получить информацию о компании",
    description="Возвращает детальную информацию о компании по её ID.",
    responses={404: {"description": "Компания не найдена"}},
    # TODO: Добавить зависимости для прав доступа (участник компании или суперадмин)
)
def read_company(
    *,
    db: Session = Depends(get_db),
    company_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user) # Пример
) -> Any:
    """
    Получить информацию о компании по ID.
    """
    company = crud.crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена",
        )
    # TODO: Проверить права доступа пользователя к этой компании
    return company

# Эндпоинт для обновления информации о компании
@router.put(
    "/{company_id}",
    response_model=schemas.Company,
    summary="Обновить информацию о компании",
    description="Обновляет данные компании по её ID.",
    responses={404: {"description": "Компания не найдена"}},
    # TODO: Добавить зависимости для прав доступа (администратор компании или суперадмин)
)
def update_company(
    *,
    db: Session = Depends(get_db),
    company_id: int,
    company_in: schemas.CompanyUpdate,
    # current_user: models.User = Depends(deps.get_current_active_admin) # Пример
) -> Any:
    """
    Обновить информацию о компании.
    Передаются только те поля, которые нужно изменить.
    """
    company = crud.crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена",
        )
    # TODO: Проверить права доступа пользователя на редактирование этой компании
    company = crud.crud_company.update(db=db, db_obj=company, obj_in=company_in)
    return company

# Эндпоинт для мягкого удаления компании
@router.delete(
    "/{company_id}",
    response_model=schemas.Company, # Возвращаем удаленную компанию для информации
    summary="Мягкое удаление компании",
    description="Деактивирует компанию (мягкое удаление).",
    responses={404: {"description": "Компания не найдена"}},
    # TODO: Добавить зависимости для прав доступа (администратор компании или суперадмин)
)
def delete_company(
    *,
    db: Session = Depends(get_db),
    company_id: int,
    # current_user: models.User = Depends(deps.get_current_active_admin) # Пример
) -> Any:
    """
    Мягкое удаление компании (деактивация).
    """
    company = crud.crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена или уже удалена",
        )
    # TODO: Проверить права доступа
    deleted_company = crud.crud_company.remove(db=db, id=company_id)
    return deleted_company # Возвращаем объект, чтобы показать, что он удален

# Эндпоинт для восстановления компании
@router.post(
    "/{company_id}/restore",
    response_model=schemas.Company,
    summary="Восстановить компанию",
    description="Восстанавливает компанию после мягкого удаления.",
    responses={404: {"description": "Удаленная компания не найдена"}},
    # TODO: Добавить зависимости для прав доступа (суперадмин)
)
def restore_company(
    *,
    db: Session = Depends(get_db),
    company_id: int,
    # current_user: models.User = Depends(deps.get_current_superuser) # Пример
) -> Any:
    """
    Восстановить мягко удаленную компанию.
    """
    restored_company = crud.crud_company.restore(db=db, id=company_id)
    if not restored_company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена или не была удалена",
        )
    # TODO: Проверить права доступа
    return restored_company

# --- Эндпоинты для Приглашений --- #

@router.post(
    "/{company_id}/invitations",
    response_model=schemas.Invitation,
    status_code=status.HTTP_201_CREATED,
    summary="Создать приглашение в компанию",
    description="Генерирует уникальный код или ссылку для приглашения пользователей.",
    # TODO: Права: администратор компании
)
def create_invitation(
    *,
    db: Session = Depends(get_db),
    invitation_in: schemas.InvitationCreate,
    company: models.Company = Depends(get_company_or_404), # Проверка компании
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
    current_user_id: int = 1 # ЗАГЛУШКА ID пользователя, создающего приглашение
) -> Any:
    """
    Создать новое приглашение.
    - **email**: Email приглашаемого (опционально, для персональных).
    - **role**: Роль назначаемая при принятии (по умолчанию 'employee').
    - **expires_at**: Срок действия (UTC, опционально, по умолчанию 7 дней).
    - **usage_limit**: Лимит использований (опционально, null/0 - безлимит).
    """
    # TODO: Проверка прав пользователя на создание приглашений в этой компании

    # Дополнительная логика:
    # - Если usage_limit не указан, и email указан -> лимит = 1 (персональное)
    # - Если usage_limit не указан, и email не указан -> лимит = null (общая ссылка)
    if invitation_in.usage_limit is None:
        if invitation_in.email:
            invitation_in.usage_limit = 1
        # else: usage_limit остается None (безлимит)

    invitation = crud.crud_invitation.create_with_company(
        db=db,
        obj_in=invitation_in,
        company_id=company.id,
        created_by_user_id=current_user_id # ЗАГЛУШКА
    )
    return invitation

# --- Эндпоинты для Статистики --- #

@router.get(
    "/{company_id}/stats",
    response_model=schemas.CompanyStats,
    summary="Получить статистику по компании",
    description="Возвращает основные статистические показатели для компании.",
    # TODO: Права: администратор компании
)
def get_company_stats(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """
    Получить статистику:
    - Общее количество активных участников.
    - Количество активных приглашений.
    - Количество опубликованных новостей.
    - Распределение активных участников по отделам.
    """
    # TODO: Проверка прав

    total_members = crud.crud_membership.count_active_by_company(db=db, company_id=company.id)
    pending_invitations = crud.crud_invitation.count_pending_by_company(db=db, company_id=company.id)
    published_news = crud.crud_news.count_published_by_company(db=db, company_id=company.id)

    # Получаем распределение по ID отделов
    member_distribution_raw = crud.crud_membership.get_distribution_by_department(db=db, company_id=company.id)

    # Получаем информацию об отделах, чтобы добавить имена
    department_ids = [dept_id for dept_id in member_distribution_raw.keys() if dept_id != -1] # Исключаем "без отдела"
    departments = {}
    if department_ids:
        department_models = db.query(models.Department).filter(
            models.Department.company_id == company.id,
            models.Department.id.in_(department_ids)
        ).all()
        departments = {dept.id: dept.name for dept in department_models}

    # Формируем финальный список распределения
    members_by_department_list: List[schemas.DepartmentMemberCount] = []
    for dept_id, count in member_distribution_raw.items():
        dept_name = departments.get(dept_id, "Без отдела") # Используем имя или "Без отдела"
        members_by_department_list.append(
            schemas.DepartmentMemberCount(
                department_id=dept_id if dept_id != -1 else None, # None вместо -1 для схемы
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