from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.db.session import get_db
from app.db.crud import (
    get_departments_by_team, create_department, update_department,
    delete_department, get_department_by_id, get_department_tree,
    get_team_by_id
)
from app.schemas.department import (
    DepartmentCreate, DepartmentResponse, DepartmentUpdate,
    OrganizationStructure, DepartmentTreeNode
)
from app.dependencies import check_team_admin, get_team_member

router = APIRouter()


@router.post("/{team_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_department(
    team_id: uuid.UUID,
    department_data: DepartmentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Создание нового отдела в команде"""
    # Проверка существования команды
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Проверка существования родительского отдела, если указан
    if department_data.parent_id:
        parent_dept = get_department_by_id(db, department_data.parent_id)
        if not parent_dept or parent_dept.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный родительский отдел не найден или не принадлежит данной команде"
            )
    
    # Создание отдела
    department = create_department(db, team_id, department_data)
    
    # Публикация события создания отдела
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_department_created,
        str(team_id),
        str(department.id),
        department.name
    )
    
    return department


@router.get("/{team_id}/departments", response_model=List[DepartmentResponse])
async def get_team_departments(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member(team_id))  # Проверка, что пользователь состоит в команде
):
    """Получение списка всех отделов команды"""
    return get_departments_by_team(db, team_id)


@router.get("/{team_id}/structure", response_model=OrganizationStructure)
async def get_organization_structure(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member(team_id))  # Проверка, что пользователь состоит в команде
):
    """Получение полной организационной структуры команды"""
    # Проверка существования команды
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Получение корневых отделов (без родителя)
    root_departments = get_department_tree(db, team_id)
    
    # Преобразование в формат дерева
    departments_tree = []
    for dept in root_departments:
        departments_tree.append(_build_department_tree(dept))
    
    return OrganizationStructure(
        team_id=team.id,
        team_name=team.name,
        departments=departments_tree
    )


def _build_department_tree(dept):
    """Рекурсивное построение дерева отделов"""
    node = DepartmentTreeNode(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        head_user_id=dept.head_user_id,
        children=[]
    )
    
    for child in dept.children:
        node.children.append(_build_department_tree(child))
    
    return node


@router.get("/{team_id}/departments/{department_id}", response_model=DepartmentResponse)
async def get_department_info(
    team_id: uuid.UUID,
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member(team_id))  # Проверка, что пользователь состоит в команде
):
    """Получение информации об отделе"""
    department = get_department_by_id(db, department_id)
    if not department or department.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден или не принадлежит указанной команде"
        )
    
    return department


@router.patch("/{team_id}/departments/{department_id}", response_model=DepartmentResponse)
async def update_department_info(
    team_id: uuid.UUID,
    department_id: uuid.UUID,
    department_data: DepartmentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Обновление информации об отделе"""
    # Проверка существования отдела
    department = get_department_by_id(db, department_id)
    if not department or department.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден или не принадлежит указанной команде"
        )
    
    # Проверка существования родительского отдела, если указан
    if department_data.parent_id and department_data.parent_id != department.parent_id:
        parent_dept = get_department_by_id(db, department_data.parent_id)
        if not parent_dept or parent_dept.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный родительский отдел не найден или не принадлежит данной команде"
            )
        
        # Проверяем, что родительский отдел не является потомком текущего (избегаем циклов)
        if _is_descendant(db, department_id, department_data.parent_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный родительский отдел является потомком текущего отдела"
            )
    
    # Обновление отдела
    updated_department = update_department(db, department_id, department_data)
    
    # Публикация события обновления отдела
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_department_updated,
        str(team_id),
        str(department_id),
        department_data.dict(exclude_unset=True)
    )
    
    return updated_department


def _is_descendant(db, parent_id, child_id):
    """Проверяет, является ли child_id потомком parent_id"""
    if parent_id == child_id:
        return True
    
    # Получаем все дочерние отделы для parent_id
    parent = get_department_by_id(db, parent_id)
    if not parent or not parent.children:
        return False
    
    for child in parent.children:
        if child.id == child_id or _is_descendant(db, child.id, child_id):
            return True
    
    return False


@router.delete("/{team_id}/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department_by_id(
    team_id: uuid.UUID,
    department_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Удаление отдела"""
    # Проверка существования отдела
    department = get_department_by_id(db, department_id)
    if not department or department.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Отдел не найден или не принадлежит указанной команде"
        )
    
    # Попытка удаления отдела
    success = delete_department(db, department_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно удалить отдел. Убедитесь, что в нем нет сотрудников и дочерних отделов."
        )
    
    # Публикация события удаления отдела
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_department_deleted,
        str(team_id),
        str(department_id)
    )
    
    return None