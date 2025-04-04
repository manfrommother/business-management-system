# task-service/app/models/__init__.py
# Импортируем все модели здесь, чтобы Alembic и Base их видели
from .task import Task
from .comment import Comment # Раскомментируем импорт Comment
from .attachment import Attachment # Раскомментируем импорт Attachment
from .evaluation import Evaluation # Раскомментируем импорт Evaluation
from .history import TaskHistory # Раскомментируем импорт History
# from .history import History # Раскомментировать при добавлении 