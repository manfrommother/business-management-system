import enum

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Если будем использовать UUID для ссылок, раскомментировать:
# import uuid
# from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

class InvitationStatus(str, enum.Enum):
    PENDING = "pending"   # Ожидает использования
    ACCEPTED = "accepted" # Принято
    EXPIRED = "expired"   # Истек срок действия
    REVOKED = "revoked"   # Отозвано администратором

class Invitation(Base):
    # Note: Имя таблицы будет 'invitations' согласно base_class
    id = Column(Integer, primary_key=True, index=True)

    # Уникальный код приглашения (может быть коротким и читаемым)
    code = Column(String(50), unique=True, index=True, nullable=False)
    # Альтернативно, можно использовать UUID для ссылки-приглашения
    # invite_uuid = Column(
    #    UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True
    # )

    # Внешний ключ к компании, к которой приглашают
    company_id = Column(Integer, ForeignKey("companys.id"), nullable=False)

    # Email пользователя, которого приглашают (если известно)
    email = Column(String(255), nullable=True, index=True)
    # Роль, назначаемая при принятии приглашения
    # TODO: Связать с MembershipRole enum?
    role = Column(String(50), nullable=False, default="employee")

    status = Column(
        Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING
    )

    # Ограничения
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Срок действия
    usage_limit = Column(Integer, nullable=True)  # Лимит использований
    times_used = Column(Integer, default=0)  # Счетчик использований

    # ID пользователя, создавшего приглашение (администратор/менеджер)
    created_by_user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    company = relationship("Company", back_populates="invitations")

    # Можно добавить связь с пользователем, принявшим приглашение
    # accepted_by_user_id = Column(
    #    Integer, ForeignKey("users.id"), nullable=True
    # ) # Или Membership ID? 