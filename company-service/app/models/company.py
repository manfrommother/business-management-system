import enum

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"  # Мягкое удаление
    PENDING_DELETION = "pending_deletion"  # Опционально, если нужен период


class Company(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    contact_info = Column(Text, nullable=True)  # Можно детализировать (JSON?)

    # Настройки
    logo_url = Column(String(512), nullable=True)
    timezone = Column(String(100), nullable=True, default="UTC")
    # Например, "Mon-Fri 9:00-18:00"
    working_hours = Column(String(255), nullable=True)
    # Например, {"primary": "#FFFFFF", "secondary": "#000000"}
    corporate_colors = Column(JSON, nullable=True)

    status = Column(Enum(CompanyStatus), default=CompanyStatus.ACTIVE, nullable=False)
    # Флаг мягкого удаления
    is_deleted = Column(Boolean, default=False)
    # Время мягкого удаления
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи (отношения определены как строки для отложенной загрузки)
    departments = relationship(
        "Department", back_populates="company", cascade="all, delete-orphan"
    )
    memberships = relationship(
        "Membership", back_populates="company", cascade="all, delete-orphan"
    )
    invitations = relationship(
        "Invitation", back_populates="company", cascade="all, delete-orphan"
    )
    news = relationship(
        "News", back_populates="company", cascade="all, delete-orphan"
    )

    # Если нужно хранить ID создателя/владельца (из User Service)
    # owner_user_id = Column(Integer, nullable=False)