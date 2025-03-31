# company-service/app/api/v1/endpoints/departments.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Позже добавим зависимости для проверки прав
from app.db.session import get_db

router = APIRouter()

# Вспомогательная функция для проверки существования компании
# (можно вынести в deps.py)
async def get_company_or_404(
    company_id: int = Path(..., description="ID компании"),
    db: Session = Depends(get_db)
) -> models.Company:
    company = crud.crud_company.get(db=db, id=company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Компания не найдена")
    return company

@router.get(
    "/",
    response_model=List[schemas.Department],
    summary="Получить список подразделений компании",
    description="Возвращает список активных подразделений для указанной компании.",
    # TODO: Права: участник компании
)
async def read_departments(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404), # Проверяем компанию
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить список подразделений компании."""
    # TODO: Проверка прав пользователя на просмотр этой компании
    departments = crud.crud_department.get_multi_by_company(
        db=db, company_id=company.id, skip=skip, limit=limit
    )
    return departments

@router.post(
    "/",
    response_model=schemas.Department,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое подразделение",
    description="Создает новое подразделение внутри указанной компании.",
    # TODO: Права: администратор компании
)
async def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: schemas.DepartmentCreate,
    company: models.Company = Depends(get_company_or_404), # Проверяем компанию
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """
    Создать новое подразделение для компании.
    - **name**: Название (обязательно)
    - **parent_department_id**: ID родительского отдела (опционально)
    - **manager_user_id**: ID руководителя (опционально)
    """
    # TODO: Проверка прав пользователя на создание в этой компании
    # TODO: Проверка существования parent_department_id и manager_user_id, если указаны
    department = crud.crud_department.create_with_company(
        db=db, obj_in=department_in, company_id=company.id
    )
    return department

@router.get(
    "/{department_id}",
    response_model=schemas.Department,
    summary="Получить информацию о подразделении",
    responses={404: {"description": "Подразделение не найдено"}},
    # TODO: Права: участник компании
)
async def read_department(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404), # Проверяем компанию
    department_id: int = Path(..., description="ID подразделения"),
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить детальную информацию о подразделении по ID."""
    # TODO: Проверка прав
    department = crud.crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")
    return department

@router.put(
    "/{department_id}",
    response_model=schemas.Department,
    summary="Обновить подразделение",
    responses={404: {"description": "Подразделение не найдено"}},
    # TODO: Права: администратор компании или руководитель отдела
)
async def update_department(
    *,
    db: Session = Depends(get_db),
    department_in: schemas.DepartmentUpdate,
    company: models.Company = Depends(get_company_or_404), # Проверяем компанию
    department_id: int = Path(..., description="ID подразделения"),
    # current_user: models.User = Depends(deps.get_current_editor(department_id)) # Пример
) -> Any:
    """
    Обновить информацию о подразделении.
    Передаются только изменяемые поля.
    """
    # TODO: Проверка прав
    department = crud.crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")
    # TODO: Дополнительные проверки (например, parent_department_id существует и в той же компании)
    updated_department = crud.crud_department.update(db=db, db_obj=department, obj_in=department_in)
    return updated_department

@router.delete(
    "/{department_id}",
    response_model=schemas.Department, # Возвращаем для информации
    summary="Архивировать подразделение",
    responses={404: {"description": "Подразделение не найдено"}},
    # TODO: Права: администратор компании
)
async def archive_department(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404), # Проверяем компанию
    department_id: int = Path(..., description="ID подразделения"),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """Архивировать (мягко удалить) подразделение."""
    # TODO: Проверка прав
    department = crud.crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")
    # TODO: Проверить, что в отделе нет активных сотрудников? Или перенести их?
    archived_department = crud.crud_department.archive(db=db, department_id=department_id)
    return archived_department

# По ТЗ нет эндпоинта для разархивации, но он может быть полезен
@router.post(
    "/{department_id}/unarchive",
    response_model=schemas.Department,
    summary="Восстановить подразделение из архива",
    responses={404: {"description": "Подразделение не найдено в архиве"}},
    # TODO: Права: администратор компании
)
async def unarchive_department(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    department_id: int = Path(..., description="ID подразделения"),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id))
) -> Any:
    """Восстановить подразделение из архива."""
    # TODO: Проверка прав
    unarchived_dep = crud.crud_department.unarchive(db=db, department_id=department_id)
    if not unarchived_dep or unarchived_dep.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Архивированное подразделение не найдено")
    return unarchived_dep 