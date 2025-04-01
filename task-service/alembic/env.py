# task-service/alembic/env.py
import os
import sys
from logging.config import fileConfig

from alembic import context

# Добавляем корень проекта (task-service) в sys.path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_path, '..')
sys.path.append(project_root)

# Импортируем Base из нашего приложения и настройки
from app.db.base_class import Base # Импортируем Base из base_class
from app.core.config import settings # Импортируем настройки

# Явный импорт моделей, чтобы убедиться, что они зарегистрированы в Base.metadata
# Это важно для автогенерации миграций
# import app.models # или импортировать каждую модель отдельно
# from app.models.task import Task
# from app.models.comment import Comment
# ... и т.д.

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Указываем Alembic на метаданные наших моделей
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Получаем URL напрямую из настроек, а не из ini файла
    url = settings.DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Добавляем render_as_batch для поддержки SQLite и некоторых операций ALTER в других БД
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Импортируем движок из нашего приложения
    from app.db.session import engine

    # Используем наш настроенный движок
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Добавляем render_as_batch
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 