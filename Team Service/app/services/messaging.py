import json
import logging
import aio_pika
import asyncio
from typing import Dict, Any, Optional
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)

# Константы
EXCHANGE_NAME = "team_events"
EVENT_TYPE_FIELD = "event"

# Кастомный JSON энкодер для datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class RabbitMQService:
    def __init__(self):
        """Инициализация сервиса RabbitMQ"""
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._is_connecting = False
        self._connection_lock = asyncio.Lock()
    
    async def connect(self):
        """Подключение к RabbitMQ"""
        if self.connection is None or self.connection.is_closed:
            # Защита от гонки при параллельных вызовах connect()
            async with self._connection_lock:
                if self._is_connecting:
                    logger.debug("Подключение к RabbitMQ уже выполняется, ожидание...")
                    return
                
                self._is_connecting = True
                try:
                    logger.info("Подключение к RabbitMQ...")
                    try:
                        self.connection = await aio_pika.connect_robust(
                            host=settings.RABBITMQ_HOST,
                            port=int(settings.RABBITMQ_PORT),
                            login=settings.RABBITMQ_USER,
                            password=settings.RABBITMQ_PASSWORD
                        )
                        self.channel = await self.connection.channel()
                        self.exchange = await self.channel.declare_exchange(
                            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC
                        )
                        logger.info("Подключено к RabbitMQ")
                    except aio_pika.exceptions.AMQPException as e:
                        logger.error(f"Ошибка подключения к RabbitMQ: {str(e)}")
                        self._reset_connection()
                        raise
                finally:
                    self._is_connecting = False
        else:
            logger.debug("Соединение с RabbitMQ уже установлено")
    
    def _reset_connection(self):
        """Сброс всех полей соединения"""
        self.connection = None
        self.channel = None
        self.exchange = None
    
    async def close(self):
        """Закрытие соединения с RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Отключено от RabbitMQ")
            self._reset_connection()
    
    async def publish_message(self, routing_key: str, message: Dict[str, Any]):
        """Публикация сообщения в RabbitMQ"""
        if self.exchange is None:
            await self.connect()
        
        try:
            # Добавляем тип события, если его нет
            if EVENT_TYPE_FIELD not in message:
                message[EVENT_TYPE_FIELD] = routing_key.split('.')[-1]
                
            message_body = json.dumps(message, cls=DateTimeEncoder).encode()
            await self.exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    content_type="application/json"
                ),
                routing_key=routing_key
            )
            logger.info(f"Опубликовано сообщение по ключу маршрутизации {routing_key}")
            return True
        except Exception as e:
            logger.critical(f"Критическая ошибка публикации сообщения: {str(e)}")
            return False
    
    # === Team Events ===
    
    async def publish_team_created(self, team_id: str, team_name: str, creator_id: str):
        """Публикация события создания команды"""
        await self.publish_message(
            "team.created",
            {
                "team_id": team_id,
                "team_name": team_name,
                "creator_id": creator_id,
                EVENT_TYPE_FIELD: "created"
            }
        )
    
    async def publish_team_updated(self, team_id: str, updated_fields: Dict[str, Any]):
        """Публикация события обновления команды"""
        await self.publish_message(
            "team.updated",
            {
                "team_id": team_id,
                "updated_fields": updated_fields,
                EVENT_TYPE_FIELD: "updated"
            }
        )
    
    async def publish_team_deleted(self, team_id: str, deleted_by: str):
        """Публикация события удаления команды"""
        await self.publish_message(
            "team.deleted",
            {
                "team_id": team_id,
                "deleted_by": deleted_by,
                EVENT_TYPE_FIELD: "deleted"
            }
        )
    
    # === Department Events ===
    
    async def publish_department_created(self, team_id: str, department_id: str, department_name: str):
        """Публикация события создания отдела"""
        await self.publish_message(
            "department.created",
            {
                "team_id": team_id,
                "department_id": department_id,
                "department_name": department_name,
                EVENT_TYPE_FIELD: "created"
            }
        )
    
    async def publish_department_updated(self, team_id: str, department_id: str, updated_fields: Dict[str, Any]):
        """Публикация события обновления отдела"""
        await self.publish_message(
            "department.updated",
            {
                "team_id": team_id,
                "department_id": department_id,
                "updated_fields": updated_fields,
                EVENT_TYPE_FIELD: "updated"
            }
        )
    
    async def publish_department_deleted(self, team_id: str, department_id: str):
        """Публикация события удаления отдела"""
        await self.publish_message(
            "department.deleted",
            {
                "team_id": team_id,
                "department_id": department_id,
                EVENT_TYPE_FIELD: "deleted"
            }
        )
    
    # === Member Events ===
    
    async def publish_member_added(self, team_id: str, user_id: str, role: str):
        """Публикация события добавления участника в команду"""
        await self.publish_message(
            "member.added",
            {
                "team_id": team_id,
                "user_id": user_id,
                "role": role,
                EVENT_TYPE_FIELD: "added"
            }
        )
    
    async def publish_member_updated(self, team_id: str, user_id: str, updated_fields: Dict[str, Any]):
        """Публикация события обновления информации об участнике"""
        await self.publish_message(
            "member.updated",
            {
                "team_id": team_id,
                "user_id": user_id,
                "updated_fields": updated_fields,
                EVENT_TYPE_FIELD: "updated"
            }
        )
    
    async def publish_member_removed(self, team_id: str, user_id: str):
        """Публикация события удаления участника из команды"""
        await self.publish_message(
            "member.removed",
            {
                "team_id": team_id,
                "user_id": user_id,
                EVENT_TYPE_FIELD: "removed"
            }
        )
    
    async def publish_member_joined(self, team_id: str, user_id: str, role: str):
        """Публикация события присоединения участника к команде по инвайту"""
        await self.publish_message(
            "member.joined",
            {
                "team_id": team_id,
                "user_id": user_id,
                "role": role,
                EVENT_TYPE_FIELD: "joined"
            }
        )
    
    # === News Events ===
    
    async def publish_news_created(self, team_id: str, news_id: str, news_title: str):
        """Публикация события создания новости"""
        await self.publish_message(
            "news.created",
            {
                "team_id": team_id,
                "news_id": news_id,
                "news_title": news_title,
                EVENT_TYPE_FIELD: "created"
            }
        )
    
    async def publish_news_updated(self, team_id: str, news_id: str, news_title: str):
        """Публикация события обновления новости"""
        await self.publish_message(
            "news.updated",
            {
                "team_id": team_id,
                "news_id": news_id,
                "news_title": news_title,
                EVENT_TYPE_FIELD: "updated"
            }
        )
    
    async def publish_news_deleted(self, team_id: str, news_id: str):
        """Публикация события удаления новости"""
        await self.publish_message(
            "news.deleted",
            {
                "team_id": team_id,
                "news_id": news_id,
                EVENT_TYPE_FIELD: "deleted"
            }
        )


# Создание синглтон-экземпляра с использованием lru_cache
@lru_cache()
def get_rabbitmq_service() -> RabbitMQService:
    """Получение синглтон-экземпляра RabbitMQService"""
    return RabbitMQService()

# Для обратной совместимости
rabbitmq_service = get_rabbitmq_service()