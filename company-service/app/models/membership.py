import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint

from app.db.base_class import Base

class MembershipRole(str, enum.Enum):
    ADMIN = "admin"        # Администратор компании
    MANAGER = "manager"    # Менеджер (например, руководитель отдела)
    EMPLOYEE = "employee"  # Сотрудник

class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"      # Активен
    INACTIVE = "inactive"  # Неактивен (отключен)
    PENDING = "pending"    # Ожидает принятия приглашения (если используется)

class Membership(Base):
    id = Column(Integer, primary_key=True, index=True)

    # ID пользователя из User Service
    user_id = Column(Integer, nullable=False, index=True)

    # Внешний ключ к компании
    company_id = Column(Integer, ForeignKey("companys.id"), nullable=False)
    # Внешний ключ к подразделению (nullable, если сотрудник не в отделе)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    role = Column(Enum(MembershipRole), nullable=False, default=MembershipRole.EMPLOYEE)
    status = Column(Enum(MembershipStatus), nullable=False, default=MembershipStatus.ACTIVE)

    join_date = Column(DateTime(timezone=True), server_default=func.now())
    # Можно добавить дату ухода/деактивации
    # leave_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    company = relationship("Company", back_populates="memberships")
    department = relationship("Department", back_populates="memberships")

    # Ограничение: один пользователь может быть членом одной компании только один раз
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name='uq_user_company'),
    ) 