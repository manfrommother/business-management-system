import json
import logging
import aio_pika
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        
    async def connect(self):
        """Подключение к RabbitMQ"""
        if self.connection is None or self.connection.is_closed:
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
                    "user_events", aio_pika.ExchangeType.TOPIC
                )
                logger.info("Подключено к RabbitMQ")
            except Exception as e:
                logger.error(f"Ошибка подключения к RabbitMQ: {str(e)}")
                self.connection = None
                self.channel = None
                self.exchange = None
                raise
    
    async def close(self):
        """Закрывает соединения с RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Отключено от RabbitMQ")
    
    async def publish_message(self, routing_key: str, message: Dict[str, Any]):
        """Публикует сообщения в RabbitMQ"""
        if self.exchange is None:
            await self.connect()
        
        try:
            message_body = json.dumps(message).encode()
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
            logger.error(f"Ошибка публикации сообщения: {str(e)}")
            return False
    
    async def publish_user_created(self, user_id: str, email: str, name: str):
        """Публикует события создания пользователя"""
        await self.publish_message(
            "user.created",
            {
                "user_id": user_id,
                "email": email,
                "name": name,
                "event": "created"
            }
        )
    
    async def publish_user_updated(self, user_id: str, updated_fields: Dict[str, Any]):
        """Публикует события обновления пользователя"""
        await self.publish_message(
            "user.updated",
            {
                "user_id": user_id,
                "updated_fields": updated_fields,
                "event": "updated"
            }
        )
    
    async def publish_user_deleted(self, user_id: str):
        """Публикует события удаления пользователя"""
        await self.publish_message(
            "user.deleted",
            {
                "user_id": user_id,
                "event": "deleted"
            }
        )
    
    async def publish_user_restored(self, user_id: str):
        """Публикует события восстановления пользователя"""
        await self.publish_message(
            "user.restored",
            {
                "user_id": user_id,
                "event": "restored"
            }
        )

# Создание синглтон-экземпляра
rabbitmq_service = RabbitMQService()