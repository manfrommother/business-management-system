# task-service/app/core/messaging.py
import pika
import json
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session # Импортируем Session

from app.core.config import settings
from app.db.session import SessionLocal # Для доступа к БД
from app.crud import crud_task # Импортируем CRUD операции для задач

logger = logging.getLogger(__name__)

connection = None
channel = None

# Имена обменников, которые мы слушаем (предполагаемые)
USER_EVENTS_EXCHANGE = "user_events"
TEAM_EVENTS_EXCHANGE = "team_events"
TASK_SERVICE_QUEUE = "task_service_queue"  # Имя нашей очереди

def get_rabbitmq_connection():
    """Устанавливает (или переиспользует) соединение с RabbitMQ."""
    global connection
    if connection and connection.is_open:
        return connection
    
    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        # Добавляем heartbeat для поддержания соединения
        heartbeat=600, # 10 минут
        blocked_connection_timeout=300 # 5 минут
    )
    try:
        connection = pika.BlockingConnection(parameters)
        logger.info("Successfully connected to RabbitMQ.")
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        connection = None
        return None

def get_rabbitmq_channel():
    """Получает канал RabbitMQ, устанавливая соединение при необходимости."""
    global channel
    conn = get_rabbitmq_connection()
    if not conn:
        return None
        
    if channel and channel.is_open:
        return channel
        
    try:
        channel = conn.channel()
        # Объявляем обменник (тип fanout - рассылает всем подписчикам)
        # durable=True - обменник переживет перезапуск RabbitMQ
        channel.exchange_declare(
            exchange=settings.RABBITMQ_EXCHANGE_NAME, 
            exchange_type='fanout',
            durable=True 
        )
        logger.info(f"RabbitMQ channel obtained and exchange '{settings.RABBITMQ_EXCHANGE_NAME}' declared.")
        return channel
    except pika.exceptions.AMQPChannelError as e:
        logger.error(f"Failed to open RabbitMQ channel: {e}")
        channel = None
        connection = None # Закрываем и соединение при ошибке канала
        return None

def publish_message(routing_key: str, message_body: Dict[str, Any]):
    """
    Публикует сообщение в настроенный обменник RabbitMQ.
    
    Args:
        routing_key: Ключ маршрутизации (для fanout не используется, но может понадобиться для других типов).
        message_body: Тело сообщения (словарь Python).
    """
    ch = get_rabbitmq_channel()
    if not ch:
        logger.error("Cannot publish message: RabbitMQ channel is not available.")
        return False

    try:
        # Сериализуем сообщение в JSON строку
        message_json = json.dumps(message_body, default=str) # default=str для обработки datetime и др.
        
        ch.basic_publish(
            exchange=settings.RABBITMQ_EXCHANGE_NAME,
            routing_key=routing_key, # Для fanout можно оставить пустым
            body=message_json,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # Делает сообщение персистентным (если очередь durable)
            )
        )
        logger.info(f"Message published to exchange '{settings.RABBITMQ_EXCHANGE_NAME}' with routing key '{routing_key}'")
        return True
    except Exception as e:
        logger.error(f"Failed to publish message to RabbitMQ: {e}")
        # Можно попытаться переподключиться или просто вернуть False
        global channel, connection
        channel = None
        connection = None
        return False

def close_rabbitmq_connection():
    """Закрывает соединение с RabbitMQ."""
    global connection, channel
    if channel and channel.is_open:
        try:
            channel.close()
            logger.info("RabbitMQ channel closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ channel: {e}")
    if connection and connection.is_open:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
             logger.error(f"Error closing RabbitMQ connection: {e}")
    channel = None
    connection = None

def declare_and_bind_queue(ch):
    """Объявляет очередь для Task Service и привязывает к обменникам."""
    try:
        # Объявляем очередь (durable=True - очередь переживет перезапуск RabbitMQ)
        ch.queue_declare(queue=TASK_SERVICE_QUEUE, durable=True)
        logger.info(f"Queue '{TASK_SERVICE_QUEUE}' declared.")

        # Привязка к обменнику событий пользователей
        # durable=True - обменник должен быть объявлен как durable тем,
        # кто его создал (User Service)
        ch.exchange_declare(
            exchange=USER_EVENTS_EXCHANGE, exchange_type='topic', durable=True
        )
        # Слушаем все события пользователей (routing_key='#')
        # или конкретные (e.g., 'user.updated')
        ch.queue_bind(
            exchange=USER_EVENTS_EXCHANGE, queue=TASK_SERVICE_QUEUE, routing_key='#'
        )
        logger.info(
            f"Queue '{TASK_SERVICE_QUEUE}' bound to exchange "
            f"'{USER_EVENTS_EXCHANGE}' with key '#'."
        )

        # Привязка к обменнику событий команд
        ch.exchange_declare(
            exchange=TEAM_EVENTS_EXCHANGE, exchange_type='topic', durable=True
        )
        ch.queue_bind(
            exchange=TEAM_EVENTS_EXCHANGE, queue=TASK_SERVICE_QUEUE, routing_key='#'
        )
        logger.info(
            f"Queue '{TASK_SERVICE_QUEUE}' bound to exchange "
            f"'{TEAM_EVENTS_EXCHANGE}' with key '#'."
        )

        return True
    except Exception as e:
        logger.error(f"Error declaring/binding queue '{TASK_SERVICE_QUEUE}': {e}")
        return False

def message_callback(ch, method, properties, body):
    """Обработчик входящих сообщений RabbitMQ."""
    routing_key = method.routing_key
    db: Session = SessionLocal() # Получаем сессию БД
    try:
        message = json.loads(body.decode('utf-8'))
        logger.info(f"Received message with routing key '{routing_key}': {message}")

        # --- Логика обработки сообщений --- #
        if routing_key == "company.deleted":
            company_id = message.get("id")
            if company_id:
                logger.info(f"Processing company.deleted for company_id: {company_id}")
                try:
                    deleted_count = crud_task.task.delete_by_company_id(db=db, company_id=company_id) # Используем crud_task.task
                    db.commit() # Фиксируем удаление
                    logger.info(f"Successfully deleted {deleted_count} tasks for deleted company {company_id}.")
                except Exception as e_crud:
                    logger.error(f"Error deleting tasks for company {company_id}: {e_crud}")
                    db.rollback() # Откатываем транзакцию при ошибке
            else:
                logger.warning("Received company.deleted event without 'id'.")

        elif routing_key == "user.deleted":
            user_id = message.get("id")
            if user_id:
                logger.info(f"Processing user.deleted for user_id: {user_id}")
                try:
                    unassigned_count = crud_task.task.unassign_by_user_id(db=db, user_id=user_id) # Используем crud_task.task
                    db.commit() # Фиксируем снятие назначений
                    logger.info(f"Successfully unassigned {unassigned_count} tasks from deleted user {user_id}.")
                except Exception as e_crud:
                    logger.error(f"Error unassigning tasks for user {user_id}: {e_crud}")
                    db.rollback() # Откатываем транзакцию
            else:
                logger.warning("Received user.deleted event without 'id'.")

        # TODO: Добавить обработку других событий (user.updated, team.*, etc.)
        # elif routing_key == "user.updated": ...
        # elif routing_key.startswith("team."): ...
        else:
            logger.warning(f"Received message with unhandled routing key: {routing_key}")

        # Подтверждаем успешную обработку сообщения RabbitMQ
        # Делаем это только если вся обработка внутри try прошла успешно
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.debug(f"Message acknowledged for routing key: {routing_key}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON message body: {e}. Body: {body[:100]}...")
        # Отклоняем сообщение без повторной постановки в очередь
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Generic error processing message with routing key '{routing_key}': {e}", exc_info=True)
        db.rollback() # Откатываем транзакцию БД на всякий случай
        # Отклоняем сообщение без повторной постановки в очередь, т.к. ошибка скорее всего системная
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close() # Всегда закрываем сессию

def start_consuming():
    """Запускает процесс потребления сообщений из очереди."""
    logger.info("Starting RabbitMQ consumer...")
    ch = get_rabbitmq_channel()
    if not ch:
        logger.error("Cannot start consumer: RabbitMQ channel is not available.")
        return

    if not declare_and_bind_queue(ch):
        logger.error("Cannot start consumer: Failed to declare/bind queue.")
        return

    # Указываем, что будем потреблять сообщения из нашей очереди
    # auto_ack=False - подтверждение обработки вручную (через basic_ack/basic_nack)
    ch.basic_consume(queue=TASK_SERVICE_QUEUE, on_message_callback=message_callback, auto_ack=False)

    logger.info("Consumer started. Waiting for messages...")
    try:
        # Запуск бесконечного цикла ожидания сообщений
        # Этот вызов блокирующий
        ch.start_consuming()
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user.")
    except Exception as e:
        logger.error(f"Consumer stopped due to an error: {e}")
    finally:
        # Закрываем соединение при остановке потребителя
        logger.info("Closing RabbitMQ connection...")
        close_rabbitmq_connection()

# Пример использования:
# def some_function():
#     message = {"task_id": 1, "status": "done"}
#     publish_message(routing_key="task.completed", message_body=message)

# Соединение можно инициализировать при старте и закрывать при остановке приложения
# в lifespan (main.py)

# Потребителя (start_consuming) обычно запускают как отдельный процесс/скрипт. 