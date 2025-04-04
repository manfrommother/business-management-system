# company-service/app/api/v1/endpoints/departments.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Импортируем зависимости
from app.db.session import get_db
# Убираем get_company_or_404, т.к. проверка будет в deps
# from .departments import get_company_or_404
# Импортируем CRUD напрямую
from app.crud import crud_department

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Department],
    summary="Получить список подразделений компании",
    description="Возвращает список активных подразделений для указанной компании.",
    responses={403: {"description": "Доступ запрещен"}},
)
async def read_departments(
    *,
    # company_id из Path будет передан в get_current_member
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_member), # Проверяем членство
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Получить список подразделений компании (доступно участникам)."""
    # Права проверены, company_id есть в membership.company_id
    departments = crud_department.get_multi_by_company(
        db=db, company_id=membership.company_id, skip=skip, limit=limit
    )
    return departments

@router.post(
    "/",
    response_model=schemas.Department,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое подразделение",
    description="Создает новое подразделение внутри указанной компании.",
    responses={403: {"description": "Доступ запрещен (требуется админ/менеджер)"}},
)
async def create_department(
    *,
    # company_id из Path будет передан в get_current_company_manager
    db: Session = Depends(get_db),
    department_in: schemas.DepartmentCreate,
    # Требуем права менеджера или админа компании
    membership: models.Membership = Depends(deps.get_current_company_manager),
) -> Any:
    """
    Создать новое подразделение для компании (доступно админам/менеджерам).
    - **name**: Название (обязательно)
    - **parent_department_id**: ID родительского отдела (опционально)
    - **manager_user_id**: ID руководителя (опционально)
    """
    # Права проверены, company_id есть в membership.company_id
    company_id = membership.company_id

    # Проверка parent_department_id
    if department_in.parent_department_id:
        parent_dept = crud_department.get(
            db, department_id=department_in.parent_department_id
        )
        if not parent_dept or parent_dept.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Родительское подразделение с ID {department_in.parent_department_id} не найдено в этой компании."
            )
        # Доп. проверка: нельзя сделать отдел родительским для самого себя
        # (хотя это и так не пройдет при update, но лучше проверить)
        # А также проверка на циклические зависимости (сложнее, пока пропускаем)

    # TODO: Проверка manager_user_id (существование пользователя и его членство в компании)
    # Это потребует обращения к User Service или локальной таблице Users/Memberships

    department = crud_department.create_with_company(
        db=db, obj_in=department_in, company_id=company_id
    )
    return department

@router.get(
    "/{department_id}",
    response_model=schemas.Department,
    summary="Получить информацию о подразделении",
    responses={
        404: {"description": "Подразделение не найдено"},
        403: {"description": "Доступ запрещен"}
    },
)
async def read_department(
    *,
    # company_id из Path будет передан в get_current_member
    db: Session = Depends(get_db),
    department_id: int = Path(..., description="ID подразделения"),
    membership: models.Membership = Depends(deps.get_current_member), # Проверяем членство
) -> Any:
    """Получить детальную информацию о подразделении (доступно участникам)."""
    # Права проверены
    department = crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")
    return department

@router.put(
    "/{department_id}",
    response_model=schemas.Department,
    summary="Обновить подразделение",
    responses={
        404: {"description": "Подразделение не найдено"},
        403: {"description": "Доступ запрещен (требуется админ/менеджер)"}
    },
)
async def update_department(
    *,
    # company_id из Path будет передан в get_current_company_manager
    db: Session = Depends(get_db),
    department_in: schemas.DepartmentUpdate,
    department_id: int = Path(..., description="ID подразделения"),
    membership: models.Membership = Depends(deps.get_current_company_manager),
) -> Any:
    """
    Обновить информацию о подразделении (доступно админам/менеджерам).
    Передаются только изменяемые поля.
    """
    # Права проверены
    company_id = membership.company_id
    department = crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")

    # Проверка parent_department_id, если он передается
    update_data = department_in.model_dump(exclude_unset=True)
    if "parent_department_id" in update_data:
        parent_id = update_data["parent_department_id"]
        if parent_id:
            # Нельзя назначить самого себя родителем
            if parent_id == department.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Подразделение не может быть родительским для самого себя."
                )

            parent_dept = crud_department.get(db, department_id=parent_id)
            if not parent_dept or parent_dept.company_id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Родительское подразделение с ID {parent_id} не найдено в этой компании."
                )
            # TODO: Проверка на создание циклической зависимости
        else: # Если parent_id = None (перемещаем в корень)
             pass

    # TODO: Проверка manager_user_id (аналогично create_department)

    updated_department = crud_department.update(db=db, db_obj=department, obj_in=department_in)
    return updated_department

@router.delete(
    "/{department_id}",
    response_model=schemas.Department,
    summary="Архивировать подразделение",
    responses={
        404: {"description": "Подразделение не найдено"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
async def archive_department(
    *,
    # company_id из Path будет передан в get_current_company_admin
    db: Session = Depends(get_db),
    department_id: int = Path(..., description="ID подразделения"),
    membership: models.Membership = Depends(deps.get_current_company_admin),
) -> Any:
    """Архивировать (мягко удалить) подразделение (доступно админам)."""
    # Права проверены
    department = crud_department.get(db=db, department_id=department_id)
    if not department or department.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подразделение не найдено")

    # TODO: Проверить, что в отделе нет активных сотрудников? Или перенести их?
    # Эта логика может быть сложной (например, требовать выбора нового отдела для сотрудников).
    # Пока пропускаем эту проверку. Администратор должен вручную убедиться.

    archived_department = crud_department.archive(db=db, department_id=department_id)
    if not archived_department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не удалось архивировать подразделение")
    return archived_department

@router.post(
    "/{department_id}/unarchive",
    response_model=schemas.Department,
    summary="Восстановить подразделение из архива",
    responses={
        404: {"description": "Подразделение не найдено в архиве"},
        403: {"description": "Доступ запрещен (требуется админ)"}
    },
)
async def unarchive_department(
    *,
    # company_id из Path будет передан в get_current_company_admin
    db: Session = Depends(get_db),
    department_id: int = Path(..., description="ID подразделения"),
    membership: models.Membership = Depends(deps.get_current_company_admin),
) -> Any:
    """Восстановить подразделение из архива (доступно админам)."""
    # Права проверены
    unarchived_dep = crud_department.unarchive(db=db, department_id=department_id)
    if not unarchived_dep or unarchived_dep.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Архивированное подразделение не найдено")
    return unarchived_dep 