from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
import uuid
import secrets
import string

from app.db.models import Team, Department, TeamMember, TeamInvite, TeamNews, MemberRole
from app.schemas import team as team_schemas
from app.schemas import department as department_schemas
from app.schemas import member as member_schemas
from app.schemas import news as news_schemas


# ===== Команды (Teams) =====

def get_team_by_id(db: Session, team_id: uuid.UUID) -> Optional[Team]:
    """Получение команды по ID"""
    return db.query(Team).filter(Team.id == team_id, Team.is_deleted == False).first()


def get_teams(db: Session, skip: int = 0, limit: int = 100) -> List[Team]:
    """Получение списка всех команд"""
    return db.query(Team).filter(Team.is_deleted == False).offset(skip).limit(limit).all()


def create_team(db: Session, team_data: team_schemas.TeamCreate, creator_id: uuid.UUID) -> Team:
    """Создание новой команды"""
    db_team = Team(**team_data.dict())
    db.add(db_team)
    db.flush()
    
    # Создаем корневой отдел для команды
    root_department = Department(
        team_id=db_team.id,
        name="Главный отдел",
        description="Корневой отдел команды",
        head_user_id=creator_id
    )
    db.add(root_department)
    db.flush()
    
    # Добавляем создателя как администратора команды
    team_member = TeamMember(
        team_id=db_team.id,
        user_id=creator_id,
        department_id=root_department.id,
        role=MemberRole.ADMIN
    )
    db.add(team_member)
    
    db.commit()
    db.refresh(db_team)
    return db_team


def update_team(db: Session, team_id: uuid.UUID, team_data: team_schemas.TeamUpdate) -> Optional[Team]:
    """Обновление данных команды"""
    db_team = get_team_by_id(db, team_id)
    if not db_team:
        return None
    
    team_data_dict = team_data.dict(exclude_unset=True)
    for field, value in team_data_dict.items():
        setattr(db_team, field, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team


def delete_team(db: Session, team_id: uuid.UUID) -> Optional[Team]:
    """Пометка команды как удаленной"""
    db_team = get_team_by_id(db, team_id)
    if not db_team:
        return None
    
    db_team.mark_deleted()
    db.commit()
    db.refresh(db_team)
    return db_team


# ===== Отделы (Departments) =====

def get_department_by_id(db: Session, department_id: uuid.UUID) -> Optional[Department]:
    """Получение отдела по ID"""
    return db.query(Department).filter(Department.id == department_id).first()


def get_departments_by_team(db: Session, team_id: uuid.UUID) -> List[Department]:
    """Получение всех отделов команды"""
    return db.query(Department).filter(Department.team_id == team_id).all()


def create_department(
    db: Session, 
    team_id: uuid.UUID, 
    department_data: department_schemas.DepartmentCreate
) -> Department:
    """Создание нового отдела в команде"""
    db_department = Department(team_id=team_id, **department_data.dict())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


def update_department(
    db: Session, 
    department_id: uuid.UUID, 
    department_data: department_schemas.DepartmentUpdate
) -> Optional[Department]:
    """Обновление данных отдела"""
    db_department = get_department_by_id(db, department_id)
    if not db_department:
        return None
    
    department_data_dict = department_data.dict(exclude_unset=True)
    for field, value in department_data_dict.items():
        setattr(db_department, field, value)
    
    db.commit()
    db.refresh(db_department)
    return db_department


def delete_department(db: Session, department_id: uuid.UUID) -> bool:
    """Удаление отдела"""
    db_department = get_department_by_id(db, department_id)
    if not db_department:
        return False
    
    # Проверяем, есть ли сотрудники в этом отделе
    members_count = db.query(TeamMember).filter(TeamMember.department_id == department_id).count()
    if members_count > 0:
        return False
    
    # Проверяем, есть ли дочерние отделы
    child_departments = db.query(Department).filter(Department.parent_id == department_id).count()
    if child_departments > 0:
        return False
    
    db.delete(db_department)
    db.commit()
    return True


def get_department_tree(db: Session, team_id: uuid.UUID) -> List[Department]:
    """Получение всех отделов команды с загрузкой связей для построения дерева"""
    return db.query(Department).filter(
        Department.team_id == team_id,
        Department.parent_id.is_(None)
    ).options(joinedload(Department.children).joinedload(Department.children)).all()


# ===== Участники команды (Team Members) =====

def get_member_by_id(db: Session, member_id: uuid.UUID) -> Optional[TeamMember]:
    """Получение участника команды по ID"""
    return db.query(TeamMember).filter(TeamMember.id == member_id).first()


def get_member_by_user_and_team(
    db: Session, 
    user_id: uuid.UUID, 
    team_id: uuid.UUID
) -> Optional[TeamMember]:
    """Получение участника по ID пользователя и ID команды"""
    return db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id
    ).first()


def get_team_members(
    db: Session, 
    team_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[TeamMember]:
    """Получение списка всех участников команды"""
    return db.query(TeamMember).filter(
        TeamMember.team_id == team_id
    ).offset(skip).limit(limit).all()


def create_team_member(
    db: Session, 
    team_id: uuid.UUID, 
    member_data: member_schemas.TeamMemberCreate
) -> TeamMember:
    """Добавление нового участника в команду"""
    db_member = TeamMember(team_id=team_id, **member_data.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def update_team_member(
    db: Session, 
    member_id: uuid.UUID, 
    member_data: member_schemas.TeamMemberUpdate
) -> Optional[TeamMember]:
    """Обновление данных участника команды"""
    db_member = get_member_by_id(db, member_id)
    if not db_member:
        return None
    
    member_data_dict = member_data.dict(exclude_unset=True)
    for field, value in member_data_dict.items():
        setattr(db_member, field, value)
    
    db.commit()
    db.refresh(db_member)
    return db_member


def delete_team_member(db: Session, member_id: uuid.UUID) -> bool:
    """Удаление участника из команды"""
    db_member = get_member_by_id(db, member_id)
    if not db_member:
        return False
    
    db.delete(db_member)
    db.commit()
    return True


def get_user_teams(db: Session, user_id: uuid.UUID) -> List[Tuple[Team, TeamMember]]:
    """Получение всех команд пользователя с его ролями"""
    return db.query(Team, TeamMember).join(
        TeamMember, Team.id == TeamMember.team_id
    ).filter(
        TeamMember.user_id == user_id,
        Team.is_deleted == False,
        TeamMember.is_active == True
    ).all()


# ===== Приглашения в команду (Team Invites) =====

def generate_invite_code(length: int = 10) -> str:
    """Генерация уникального кода приглашения"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_team_invite(
    db: Session, 
    team_id: uuid.UUID, 
    invite_data: team_schemas.TeamInviteCreate,
    created_by: uuid.UUID
) -> TeamInvite:
    """Создание приглашения в команду"""
    expires_at = datetime.utcnow() + timedelta(days=invite_data.expires_days)
    
    # Генерация уникального кода приглашения
    code = generate_invite_code()
    
    db_invite = TeamInvite(
        team_id=team_id,
        code=code,
        email=invite_data.email,
        department_id=invite_data.department_id,
        role=invite_data.role,
        created_by=created_by,
        expires_at=expires_at
    )
    
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    return db_invite


def get_invite_by_code(db: Session, code: str) -> Optional[TeamInvite]:
    """Получение приглашения по коду"""
    return db.query(TeamInvite).filter(TeamInvite.code == code).first()


def mark_invite_used(
    db: Session, 
    invite_id: uuid.UUID, 
    user_id: uuid.UUID
) -> Optional[TeamInvite]:
    """Пометка приглашения как использованного"""
    db_invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id).first()
    if not db_invite or db_invite.is_used or db_invite.is_expired:
        return None
    
    db_invite.is_used = True
    db_invite.used_by = user_id
    db_invite.used_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_invite)
    return db_invite


# ===== Новости команды (Team News) =====

def get_news_by_id(db: Session, news_id: uuid.UUID) -> Optional[TeamNews]:
    """Получение новости по ID"""
    return db.query(TeamNews).filter(TeamNews.id == news_id).first()


def get_team_news(
    db: Session, 
    team_id: uuid.UUID, 
    department_id: Optional[uuid.UUID] = None,
    skip: int = 0, 
    limit: int = 20
) -> List[TeamNews]:
    """Получение новостей команды, опционально фильтруя по отделу"""
    query = db.query(TeamNews).filter(TeamNews.team_id == team_id)
    
    if department_id:
        query = query.filter(
            or_(
                TeamNews.department_id == department_id,
                TeamNews.department_id.is_(None)  # Общие новости команды тоже показываем
            )
        )
    
    # Сначала закрепленные, потом по дате создания (новые вверху)
    query = query.order_by(TeamNews.is_pinned.desc(), TeamNews.created_at.desc())
    
    return query.offset(skip).limit(limit).all()


def create_team_news(
    db: Session, 
    team_id: uuid.UUID, 
    news_data: news_schemas.TeamNewsCreate,
    created_by: uuid.UUID
) -> TeamNews:
    """Создание новости в команде"""
    db_news = TeamNews(
        team_id=team_id,
        created_by=created_by,
        **news_data.dict()
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news


def update_team_news(
    db: Session, 
    news_id: uuid.UUID, 
    news_data: news_schemas.TeamNewsUpdate
) -> Optional[TeamNews]:
    """Обновление новости"""
    db_news = get_news_by_id(db, news_id)
    if not db_news:
        return None
    
    news_data_dict = news_data.dict(exclude_unset=True)
    for field, value in news_data_dict.items():
        setattr(db_news, field, value)
    
    db.commit()
    db.refresh(db_news)
    return db_news


def delete_team_news(db: Session, news_id: uuid.UUID) -> bool:
    """Удаление новости"""
    db_news = get_news_by_id(db, news_id)
    if not db_news:
        return False
    
    db.delete(db_news)
    db.commit()
    return True