# task-service/app/schemas/__init__.py
# Импортируем схемы для удобного доступа
from .task import Task, TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from .comment import Comment, CommentCreate, CommentUpdate # Добавляем импорт Comment
from .attachment import Attachment # Добавляем Attachment
from .evaluation import Evaluation, EvaluationCreate, EvaluationUpdate # Добавляем Evaluation
# Добавить другие схемы по мере их создания
# from .history import History
# ... 