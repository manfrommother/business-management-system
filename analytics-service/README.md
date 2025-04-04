# Analytics Service

Микросервис для сбора, обработки и анализа данных из других сервисов системы.

## Запуск

1.  Скопируйте `.env.example` в `.env` и заполните переменные окружения.
2.  Установите зависимости: `pip install -r requirements.txt`
3.  Запустите миграции: `alembic upgrade head`
4.  Запустите приложение: `uvicorn app.main:app --reload`
5.  Запустите воркеры Celery (если используются): `celery -A app.workers.tasks worker --loglevel=info`

## Технологии

*   Python 3.10+
*   FastAPI
*   SQLAlchemy
*   Alembic
*   PostgreSQL
*   RabbitMQ
*   Celery (или аналог)
*   Redis 