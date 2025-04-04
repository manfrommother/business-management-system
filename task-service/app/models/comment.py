from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .task import Task  # noqa: F401
    from .attachment import Attachment # noqa: F401

class Comment(Base):
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    author_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Связь с задачей
    task: Mapped["Task"] = relationship(back_populates="comments")

    # Связь с вложениями
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, task_id={self.task_id}, author_user_id={self.author_user_id})>" 