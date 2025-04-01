from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship # Закомментировано,
# пока не используется

from app.db.base_class import Base


class Calendar(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    # Может быть NULL для командных календарей
    owner_user_id = Column(Integer, index=True, nullable=True)
    # Предполагаем наличие таблицы teams
    team_id = Column(Integer, ForeignKey("teams.id"), index=True, nullable=True)
    # Предполагаем наличие таблицы departments
    department_id = Column(
        Integer, ForeignKey("departments.id"), index=True, nullable=True
    )
    # Является ли основным календарем пользователя
    is_primary = Column(Boolean, default=False)
    is_team_calendar = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи (будут добавлены позже)
    # events = relationship("Event", back_populates="calendar")