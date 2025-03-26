from datetime import datetime
import uuid
from sqlalchemy import String, Boolean, Column, DateTime, ForeignKey, Text, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


class MemberRole(str, enum.Enum):
    """Роли участников команды"""
    ADMIN = "admin"  # Администратор команды
    MANAGER = "manager"  # Менеджер (руководитель отдела)
    MEMBER = "member"  # Обычный участник


class Team(Base):
    """Модель команды (компании)"""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    settings = Column(JSONB, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    departments = relationship("Department", back_populates="team", cascade="all, delete-orphan")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    news = relationship("TeamNews", back_populates="team", cascade="all, delete-orphan")
    invites = relationship("TeamInvite", back_populates="team", cascade="all, delete-orphan")
    
    def mark_deleted(self):
        """Помечает команду как удаленную"""
        self.is_deleted = True
        self.is_active = False


class Department(Base):
    """Модель отдела команды"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    head_user_id = Column(UUID(as_uuid=True), nullable=True)  # ID руководителя отдела
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    team = relationship("Team", back_populates="departments")
    members = relationship("TeamMember", back_populates="department")
    children = relationship("Department", 
                          backref=relationship("Department", remote_side=[id]),
                          cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('team_id', 'name', name='uq_department_team_name'),
    )


class TeamMember(Base):
    """Модель участника команды"""
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # ID пользователя из User Service
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    role = Column(String, default=MemberRole.MEMBER)
    job_title = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    team = relationship("Team", back_populates="members")
    department = relationship("Department", back_populates="members")

    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )


class TeamInvite(Base):
    """Модель приглашений в команду"""
    __tablename__ = "team_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False, index=True, unique=True)
    email = Column(String, nullable=True)  # Email, если приглашение для конкретного пользователя
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    role = Column(String, default=MemberRole.MEMBER)
    created_by = Column(UUID(as_uuid=True), nullable=False)  # ID пользователя, создавшего приглашение
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(UUID(as_uuid=True), nullable=True)  # ID пользователя, использовавшего приглашение
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    team = relationship("Team", back_populates="invites")

    @property
    def is_expired(self):
        """Проверяет, истек ли срок действия инвайт-кода"""
        return datetime.utcnow() > self.expires_at


class TeamNews(Base):
    """Модель новостей команды"""
    __tablename__ = "team_news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)  # ID пользователя, создавшего новость
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    team = relationship("Team", back_populates="news")