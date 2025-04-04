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
                    "team_events", aio_pika.ExchangeType.TOPIC
                )
                logger.info("Подключено к RabbitMQ")
            except Exception as e:
                logger.error(f"Ошибка подключения к RabbitMQ: {str(e)}")
                self.connection = None
                self.channel = None
                self.exchange = None
                raise
    
    async def close(self):
        """Закрытие соединения с RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Отключено от RabbitMQ")
    
    async def publish_message(self, routing_key: str, message: Dict[str, Any]):
        """Публикация сообщения в RabbitMQ"""
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
    
    # === Team Events ===
    
    async def publish_team_created(self, team_id: str, team_name: str, creator_id: str):
        """Публикация события создания команды"""
        await self.publish_message(
            "team.created",
            {
                "team_id": team_id,
                "team_name": team_name,
                "creator_id": creator_id,
                "event": "created"
            }
        )
    
    async def publish_team_updated(self, team_id: str, updated_fields: Dict[str, Any]):
        """Публикация события обновления команды"""
        await self.publish_message(
            "team.updated",
            {
                "team_id": team_id,
                "updated_fields": updated_fields,
                "event": "updated"
            }
        )
    
    async def publish_team_deleted(self, team_id: str, deleted_by: str):
        """Публикация события удаления команды"""
        await self.publish_message(
            "team.deleted",
            {
                "team_id": team_id,
                "deleted_by": deleted_by,
                "event": "deleted"
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
                "event": "created"
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
                "event": "updated"
            }
        )
    
    async def publish_department_deleted(self, team_id: str, department_id: str):
        """Публикация события удаления отдела"""
        await self.publish_message(
            "department.deleted",
            {
                "team_id": team_id,
                "department_id": department_id,
                "event": "deleted"
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
                "event": "added"
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
                "event": "updated"
            }
        )
    
    async def publish_member_removed(self, team_id: str, user_id: str):
        """Публикация события удаления участника из команды"""
        await self.publish_message(
            "member.removed",
            {
                "team_id": team_id,
                "user_id": user_id,
                "event": "removed"
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
                "event": "joined"
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
                "event": "created"
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
                "event": "updated"
            }
        )
    
    async def publish_news_deleted(self, team_id: str, news_id: str):
        """Публикация события удаления новости"""
        await self.publish_message(
            "news.deleted",
            {
                "team_id": team_id,
                "news_id": news_id,
                "event": "deleted"
            }
        )


# Создание синглтон-экземпляра
rabbitmq_service = RabbitMQService()