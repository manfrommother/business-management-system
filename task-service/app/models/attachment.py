from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, 
                        CheckConstraint, BigInteger)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .task import Task      # noqa: F401
    from .comment import Comment  # noqa: F401

class Attachment(Base):
    __tablename__ = "task_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="Оригинальное имя файла")
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="MIME тип файла")
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, comment="Локальный путь к файлу на сервере")
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Размер файла в байтах")

    # Связь либо с задачей, либо с комментарием
    task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), 
        index=True, 
        nullable=True
    )
    comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_comments.id", ondelete="CASCADE"), 
        index=True, 
        nullable=True
    )

    # ID пользователя, загрузившего файл
    uploader_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Связи (отношения)
    task: Mapped[Optional["Task"]] = relationship(back_populates="attachments")
    comment: Mapped[Optional["Comment"]] = relationship(back_populates="attachments")

    # Ограничение: либо task_id, либо comment_id должен быть NOT NULL, но не оба
    __table_args__ = (
        CheckConstraint(
            "(task_id IS NOT NULL AND comment_id IS NULL) OR (task_id IS NULL AND comment_id IS NOT NULL)",
            name="chk_attachment_parent_link"
        ),
    )

    def __repr__(self):
        parent = f"task_id={self.task_id}" if self.task_id else f"comment_id={self.comment_id}"
        return f"<Attachment(id={self.id}, filename='{self.filename}', {parent})>" 