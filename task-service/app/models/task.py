import enum
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (Integer, String, Text, DateTime, ForeignKey,
                        Boolean, Enum as PgEnum)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .comment import Comment # noqa: F401
    from .attachment import Attachment # noqa: F401
    from .evaluation import Evaluation # noqa: F401
    from .history import TaskHistory # noqa: F401

# Определяем Enum для статуса и приоритета (можно вынести в отдельный файл enums.py)
class TaskStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    creator_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    assignee_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Опциональная привязка к отделу
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True, 
        index=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        PgEnum(TaskStatus, name="task_status_enum", create_type=False),
        default=TaskStatus.OPEN,
        nullable=False,
        index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        PgEnum(TaskPriority, name="task_priority_enum", create_type=False),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )

    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Для мягкого удаления
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Связи (добавить позже, когда будут другие модели)
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    evaluation: Mapped[Optional["Evaluation"]] = relationship( # Один-к-одному
        back_populates="task", cascade="all, delete-orphan", uselist=False
    )
    history: Mapped[List["TaskHistory"]] = relationship( # Связь с историей
        back_populates="task", cascade="all, delete-orphan"
    )
    # evaluations = relationship("Evaluation", back_populates="task", uselist=False) # Обычно одна оценка на задачу?
    # history = relationship("History", back_populates="task")

    # Для доступа к данным о пользователе/отделе/компании потребуются запросы к другим сервисам
    # или денормализация (хранение имен, например), но это выходит за рамки простой модели.

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>" 