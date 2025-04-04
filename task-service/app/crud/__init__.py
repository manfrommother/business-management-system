# task-service/app/crud/__init__.py
# Импортируем CRUD классы для удобного доступа
from .crud_task import crud_task
from .crud_comment import crud_comment
from .crud_attachment import crud_attachment
from .crud_evaluation import crud_evaluation
from .crud_history import crud_history
# Добавить другие CRUD по мере создания
# from .crud_history import crud_history
# ...

# Экспортируем конкретные экземпляры для использования в API
# (такой подход использовался в примере FastAPI)
# task = CRUDTask(Task) 