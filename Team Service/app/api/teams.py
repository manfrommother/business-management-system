from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
from typing import List

from app.db.session import get_db
from app.db.crud import (
    create_team, get_team_by_id, update_team, delete_team, 
    get_teams, create_team_invite, get_user_teams
)
from app.schemas.team import (
    TeamCreate, TeamResponse, TeamUpdate, SimpleTeamResponse,
    TeamInviteCreate, TeamInviteResponse
)
from app.dependencies import (
    get_current_user_id, get_current_user_from_token,
    check_team_admin, get_team_member
)
from app.services.redis import redis_service
from app.services.messaging import rabbitmq_service
from app.services.email import send_team_invite
from app.db.models import MemberRole

router = APIRouter()


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_team(
    team_data: TeamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """Создание новой команды"""
    # Создание команды
    team = create_team(db, team_data, current_user_id)
    
    # Кэширование данных команды
    background_tasks.add_task(
        redis_service.cache_team,
        str(team.id),
        TeamResponse.from_orm(team).dict()
    )
    
    # Публикация события создания команды
    background_tasks.add_task(
        rabbitmq_service.publish_team_created,
        str(team.id),
        team.name,
        str(current_user_id)
    )
    
    return team


@router.get("", response_model=List[SimpleTeamResponse])
async def get_user_teams_list(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """Получение списка команд текущего пользователя"""
    # Получаем все команды пользователя
    teams_with_roles = get_user_teams(db, current_user_id)
    
    # Возвращаем только объекты команд
    return [team for team, _ in teams_with_roles]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_info(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member(team_id))  # Проверка, что пользователь состоит в команде
):
    """Получение информации о команде"""
    # Попытка получить из кэша
    cached_team = await redis_service.get_cached_team(str(team_id))
    if cached_team:
        return cached_team
    
    # Если нет в кэше, получаем из БД
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Кэшируем и возвращаем
    team_data = TeamResponse.from_orm(team).dict()
    await redis_service.cache_team(str(team_id), team_data)
    
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team_info(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Обновление информации о команде"""
    updated_team = update_team(db, team_id, team_data)
    if not updated_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Инвалидация кэша
    background_tasks.add_task(
        redis_service.invalidate_team_cache,
        str(team_id)
    )
    
    # Публикация события обновления команды
    background_tasks.add_task(
        rabbitmq_service.publish_team_updated,
        str(team_id),
        team_data.dict(exclude_unset=True)
    )
    
    return updated_team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_by_id(
    team_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Пометка команды как удаленной"""
    deleted_team = delete_team(db, team_id)
    if not deleted_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Инвалидация кэша
    background_tasks.add_task(
        redis_service.invalidate_team_cache,
        str(team_id)
    )
    
    # Публикация события удаления команды
    background_tasks.add_task(
        rabbitmq_service.publish_team_deleted,
        str(team_id),
        str(current_user_id)
    )
    
    return None


@router.post("/{team_id}/invite", response_model=TeamInviteResponse)
async def create_invite_code(
    team_id: uuid.UUID,
    invite_data: TeamInviteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(check_team_admin(team_id))  # Проверка, что пользователь админ команды
):
    """Создание инвайт-кода для приглашения в команду"""
    # Проверка существования команды
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Создание инвайт-кода
    invite = create_team_invite(db, team_id, invite_data, current_user_id)
    
    # Если указан email, отправляем приглашение
    if invite.email:
        background_tasks.add_task(
            send_team_invite,
            invite.email,
            team.name,
            invite.code
        )
    
    return invite


@router.post("/join", response_model=TeamResponse)
async def join_team_by_invite(
    invite_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Присоединение к команде по инвайт-коду"""
    # Получаем инвайт-код
    from app.db.crud import get_invite_by_code, mark_invite_used, create_team_member, get_team_by_id
    
    invite = get_invite_by_code(db, invite_code)
    if not invite or invite.is_used or invite.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недействительный или истекший инвайт-код"
        )
    
    # Проверяем, что команда существует
    team = get_team_by_id(db, invite.team_id)
    if not team or team.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команда не найдена или удалена"
        )
    
    # Проверяем, что пользователь не состоит уже в этой команде
    from app.db.crud import get_member_by_user_and_team
    existing_member = get_member_by_user_and_team(db, current_user.id, team.id)
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже состоите в этой команде"
        )
    
    # Если инвайт был предназначен для конкретного email, проверяем соответствие
    if invite.email and invite.email.lower() != current_user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данный инвайт-код предназначен для другого пользователя"
        )
    
    # Добавляем пользователя в команду
    from app.schemas.member import TeamMemberCreate
    member_data = TeamMemberCreate(
        user_id=current_user.id,
        department_id=invite.department_id,
        role=invite.role
    )
    create_team_member(db, team.id, member_data)
    
    # Отмечаем инвайт как использованный
    mark_invite_used(db, invite.id, current_user.id)
    
    # Публикация события присоединения к команде
    background_tasks.add_task(
        rabbitmq_service.publish_member_joined,
        str(team.id),
        str(current_user.id),
        invite.role
    )
    
    return team