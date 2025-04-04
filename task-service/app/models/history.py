from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .task import Task  # noqa: F401

class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # ID пользователя, который внес изменение
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    
    # Какое поле было изменено (например, 'status', 'assignee_user_id', 'due_date')
    field_changed: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Старое и новое значение (храним как Text для универсальности)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Комментарий к изменению (опционально, может не использоваться)
    change_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связь с задачей
    task: Mapped["Task"] = relationship(back_populates="history")

    def __repr__(self):
        return f"<TaskHistory(id={self.id}, task_id={self.task_id}, field='{self.field_changed}')>" 