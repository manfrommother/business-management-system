import os
import sys
from logging.config import fileConfig

# Убираем неиспользуемые импорты SQLAlchemy
# from sqlalchemy import engine_from_config
# from sqlalchemy import pool

from alembic import context

# Добавляем корень проекта (company-service) в sys.path
# Это необходимо, чтобы Alembic мог найти модули приложения (app)
# Находим путь к директории, где лежит env.py (alembic/)
current_path = os.path.dirname(os.path.abspath(__file__))
# Поднимаемся на уровень выше (в company-service)
project_root = os.path.join(current_path, '..')
sys.path.append(project_root)

# Импортируем Base из нашего приложения и настройки
from app.db.base import Base
from app.core.config import settings # Импортируем настройки
# Явный импорт моделей, чтобы убедиться, что они зарегистрированы в Base.metadata
# from app.models.company import Company
# ... и т.д.

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    # Убираем явную кодировку, т.к. не помогло
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Указываем Alembic на метаданные наших моделей
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Получаем URL напрямую из настроек, а не из ini файла
    url = settings.DATABASE_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Импортируем движок из нашего приложения
    from app.db.session import engine

    # Используем наш настроенный движок
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata # Указываем метаданные
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
