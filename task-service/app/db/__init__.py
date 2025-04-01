# task-service/app/db/__init__.py
from .base_class import Base
# Импортируем все модели здесь, чтобы Base знала о них
# Например:
# from app.models.task import Task
# from app.models.comment import Comment

# Импортируем слушатели событий, чтобы они зарегистрировались
from . import listeners # noqa 