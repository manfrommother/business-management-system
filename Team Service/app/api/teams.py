from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Tuple
import logging
from pydantic import EmailStr

from app.db.session import get_db
from app.db.crud import (
    create_team, get_team_by_id, update_team, delete_team, 
    get_teams, create_team_invite, get_user_teams,
    get_invite_by_code, mark_invite_used, create_team_member,
    get_member_by_user_and_team
)
from app.schemas.team import (
    TeamCreate, TeamResponse, TeamUpdate, SimpleTeamResponse,
    TeamInviteCreate, TeamInviteResponse
)
from app.schemas.member import TeamMemberCreate
from app.dependencies import (
    get_current_user_id, get_current_user_from_token,
    check_team_admin, get_team_member
)
from app.services.redis import redis_service
from app.services.messaging import rabbitmq_service
from app.services.email import send_team_invite
from app.db.models import MemberRole

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter()


def serialize_team(team) -> Dict[str, Any]:
    """Утилита для сериализации команды в словарь"""
    return TeamResponse.from_orm(team).dict()


def extract_teams_from_tuples(teams_with_roles: List[Tuple[Any, Any]]) -> List[Any]:
    """Утилита для извлечения команд из кортежей (команда, роль)"""
    return [team for team, _ in teams_with_roles]


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_team(
    team_data: TeamCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Создание новой команды"""
    # Создание команды
    team = create_team(db, team_data, current_user_id)
    
    # Кэширование данных команды
    background_tasks.add_task(
        redis_service.cache_team,
        str(team.id),
        serialize_team(team)
    )
    
    # Публикация события создания команды
    try:
        background_tasks.add_task(
            rabbitmq_service.publish_team_created,
            str(team.id),
            team.name,
            str(current_user_id)
        )
    except Exception as e:
        logger.error(f"Ошибка при публикации события создания команды: {e}")
        # Продолжаем выполнение, так как основная операция уже выполнена
    
    return TeamResponse.from_orm(team)


@router.get("", response_model=List[SimpleTeamResponse])
async def get_user_teams_list(
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Получение списка команд текущего пользователя"""
    # Получаем все команды пользователя
    teams_with_roles = get_user_teams(db, current_user_id)
    
    # Возвращаем только объекты команд
    return extract_teams_from_tuples(teams_with_roles)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team_info(
    team_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Получение информации о команде"""
    # Попытка получить из кэша
    cached_team = await redis_service.get_cached_team(str(team_id))
    if cached_team:
        # Преобразуем словарь в объект TeamResponse
        return TeamResponse(**cached_team)
    
    # Если нет в кэше, получаем из БД
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Кэшируем и возвращаем
    team_data = serialize_team(team)
    await redis_service.cache_team(str(team_id), team_data)
    
    return TeamResponse.from_orm(team)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team_info(
    team_id: UUID,
    team_data: TeamUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
):
    """Обновление информации о команде"""
    # Проверка, что есть хотя бы одно обновляемое поле
    update_data = team_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указано ни одного поля для обновления"
        )
    
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
    try:
        background_tasks.add_task(
            rabbitmq_service.publish_team_updated,
            str(team_id),
            update_data
        )
    except Exception as e:
        logger.error(f"Ошибка при публикации события обновления команды: {e}")
        # Продолжаем выполнение, так как основная операция уже выполнена
    
    return TeamResponse.from_orm(updated_team)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_team(
    team_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
):
    """Мягкое удаление команды (установка флага is_deleted)"""
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
    try:
        background_tasks.add_task(
            rabbitmq_service.publish_team_deleted,
            str(team_id),
            str(current_user_id)
        )
    except Exception as e:
        logger.error(f"Ошибка при публикации события удаления команды: {e}")
        # Продолжаем выполнение, так как основная операция уже выполнена
    
    return None


@router.post("/{team_id}/invite", response_model=TeamInviteResponse)
async def create_invite_code(
    team_id: UUID,
    invite_data: TeamInviteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(check_team_admin())  # Проверка, что пользователь админ команды
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
        try:
            background_tasks.add_task(
                send_team_invite,
                invite.email,
                team.name,
                invite.code
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке приглашения на email {invite.email}: {e}")
            # Продолжаем выполнение, так как инвайт-код уже создан
    
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
    member_data = TeamMemberCreate(
        user_id=current_user.id,
        department_id=invite.department_id,
        role=invite.role
    )
    create_team_member(db, team.id, member_data)
    
    # Отмечаем инвайт как использованный
    mark_invite_used(db, invite.id, current_user.id)
    
    # Инвалидация кэша команды
    background_tasks.add_task(
        redis_service.invalidate_team_cache,
        str(team.id)
    )
    
    # Публикация события присоединения к команде
    try:
        background_tasks.add_task(
            rabbitmq_service.publish_member_joined,
            str(team.id),
            str(current_user.id),
            invite.role
        )
    except Exception as e:
        logger.error(f"Ошибка при публикации события присоединения к команде: {e}")
        # Продолжаем выполнение, так как основная операция уже выполнена
    
    return TeamResponse.from_orm(team)