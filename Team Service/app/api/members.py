from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.db.session import get_db
from app.db.crud import (
    get_team_members, create_team_member, update_team_member,
    delete_team_member, get_member_by_id, get_member_by_user_and_team,
    get_team_by_id, get_department_by_id
)
from app.schemas.member import (
    TeamMemberCreate, TeamMemberResponse, TeamMemberUpdate, TeamMemberWithUserInfo
)
from app.dependencies import check_team_admin, get_team_member
from app.services.user_service import get_user_info
from app.db.models import MemberRole, TeamMember

router = APIRouter()


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: uuid.UUID,
    member_data: TeamMemberCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
):
    """Добавление нового участника в команду"""
    # Проверка существования команды
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Проверка существования отдела, если указан
    if member_data.department_id:
        department = get_department_by_id(db, member_data.department_id)
        if not department or department.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный отдел не найден или не принадлежит данной команде"
            )
    
    # Проверка существования пользователя через User Service
    user_exists = await get_user_info(member_data.user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не найден"
        )
    
    # Проверка, что пользователь еще не состоит в команде
    existing_member = get_member_by_user_and_team(db, member_data.user_id, team_id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже состоит в этой команде"
        )
    
    # Добавление участника
    member = create_team_member(db, team_id, member_data)
    
    # Публикация события добавления участника
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_member_added,
        str(team_id),
        str(member_data.user_id),
        member_data.role
    )
    
    return member


@router.get("/{team_id}/members", response_model=List[TeamMemberWithUserInfo])
async def get_members_list(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Получение списка всех участников команды"""
    members = get_team_members(db, team_id)
    
    # Получаем информацию о пользователях из User Service
    result = []
    for member in members:
        user_info = await get_user_info(member.user_id)
        if user_info:
            # Объединяем данные об участнике и пользователе
            member_data = TeamMemberWithUserInfo(
                **TeamMemberResponse.from_orm(member).dict(),
                user_name=user_info.get("name", "Неизвестно"),
                user_email=user_info.get("email", "Неизвестно")
            )
            result.append(member_data)
    
    return result


@router.get("/{team_id}/members/{user_id}", response_model=TeamMemberWithUserInfo)
async def get_team_member_info(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Получение информации об участнике команды"""
    member = get_member_by_user_and_team(db, user_id, team_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден"
        )
    
    # Получаем информацию о пользователе из User Service
    user_info = await get_user_info(member.user_id)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация о пользователе не найдена"
        )
    
    # Объединяем данные об участнике и пользователе
    return TeamMemberWithUserInfo(
        **TeamMemberResponse.from_orm(member).dict(),
        user_name=user_info.get("name", "Неизвестно"),
        user_email=user_info.get("email", "Неизвестно")
    )


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member_info(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    member_data: TeamMemberUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
):
    """Обновление информации об участнике команды"""
    # Получаем информацию об участнике
    member = get_member_by_user_and_team(db, user_id, team_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден"
        )
    
    # Проверка существования отдела, если указан
    if member_data.department_id:
        department = get_department_by_id(db, member_data.department_id)
        if not department or department.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный отдел не найден или не принадлежит данной команде"
            )
    
    # Обновляем информацию об участнике
    updated_member = update_team_member(db, member.id, member_data)
    
    # Публикация события обновления участника
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_member_updated,
        str(team_id),
        str(user_id),
        member_data.dict(exclude_unset=True)
    )
    
    return updated_member


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
):
    """Удаление участника из команды"""
    # Проверка, что удаляемый пользователь не является последним администратором
    if str(user_id) == str(current_user_id):
        # Проверяем, есть ли другие администраторы в команде
        admin_count = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.role == MemberRole.ADMIN,
            TeamMember.is_active == True
        ).count()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невозможно удалить последнего администратора команды"
            )
    
    # Получаем информацию об участнике
    member = get_member_by_user_and_team(db, user_id, team_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден"
        )
    
    # Удаляем участника
    success = delete_team_member(db, member.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить участника"
        )
    
    # Публикация события удаления участника
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_member_removed,
        str(team_id),
        str(user_id)
    )
    
    return None