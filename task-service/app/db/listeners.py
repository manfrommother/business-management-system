from sqlalchemy import event
from sqlalchemy.orm import Session, object_session, attributes

from app.models.task import Task
from app.models.history import TaskHistory
from app.schemas.history import TaskHistoryCreate

# Список полей Task, изменения которых нужно отслеживать
TRACKED_TASK_FIELDS = [
    "title",
    "description",
    "assignee_user_id",
    "department_id",
    "status",
    "priority",
    "start_date",
    "due_date",
    "completion_date",
]

@event.listens_for(Task, 'before_update')
def before_task_update(mapper, connection, target: Task):
    """Слушатель события перед обновлением объекта Task."""
    db_session: Session = object_session(target)
    if not db_session:
        # Объект не привязан к сессии, невозможно отследить изменения или создать историю
        return

    # Получаем "грязные" (измененные) атрибуты
    state = attributes.instance_state(target)
    changes = {}
    user_id = None # TODO: Как получить ID пользователя, инициировавшего изменение?

    # Пытаемся получить ID пользователя из контекста сессии (если он там есть)
    # Это требует передачи user_id в сессию при обработке запроса.
    # Например, через info: db_session.info['user_id'] = current_user_id
    if hasattr(db_session, 'info') and 'user_id' in db_session.info:
        user_id = db_session.info['user_id']
    else:
        # Альтернатива: Логгировать предупреждение или использовать "системного" пользователя
        # Или отказаться от записи истории, если user_id неизвестен
        # print("Warning: User ID not found in session info for history tracking.")
        # Пока пропустим запись истории, если нет user_id
        return

    for attr in state.attrs:
        history = attr.history
        if history.has_changes() and attr.key in TRACKED_TASK_FIELDS:
            old_value = history.deleted[0] if history.deleted else None
            new_value = history.added[0] if history.added else None
            
            # Преобразуем значения в строки для сохранения в Text поле
            old_value_str = str(old_value) if old_value is not None else None
            new_value_str = str(new_value) if new_value is not None else None

            # Создаем запись истории (пока не коммитим, т.к. это before_update)
            history_entry_schema = TaskHistoryCreate(
                task_id=target.id,
                user_id=user_id,
                field_changed=attr.key,
                old_value=old_value_str,
                new_value=new_value_str
            )
            history_entry = TaskHistory(**history_entry_schema.model_dump())
            db_session.add(history_entry)
            # Запись будет добавлена в БД при db.commit() после обновления Task

# --- Регистрация слушателя --- 
# Слушатель нужно где-то импортировать, чтобы он зарегистрировался.
# Хорошее место - __init__.py пакета db или models, или даже main.py.

# Например, добавьте в task-service/app/db/__init__.py:
# from . import listeners # noqa 