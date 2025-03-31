from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base
# Возможно, понадобится enum для таргетирования по ролям
# from .membership import MembershipRole

class News(Base):
    # Note: Имя таблицы будет 'news' (не 'newss')
    # Это нужно переопределить или настроить в base_class
    __tablename__ = "news"  # Явно указываем имя таблицы

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # ID пользователя-автора из User Service
    # Может быть системное сообщение?
    author_user_id = Column(Integer, nullable=True)

    # Внешний ключ к компании
    company_id = Column(Integer, ForeignKey("companys.id"), nullable=False)

    # Таргетирование (опционально)
    target_department_id = Column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    # Если таргетируем по ролям
    # target_role = Column(Enum(MembershipRole), nullable=True)

    # Статус и планирование
    # Или False, если нужна модерация/планирование
    is_published = Column(Boolean, default=True)
    # Для отложенных публикаций
    published_at = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, default=False)

    # Медиа (пример: список URL или ссылок на объект хранилища)
    media_attachments = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    company = relationship("Company", back_populates="news")
    # Связь только в одну сторону к Department
    target_department = relationship("Department") 