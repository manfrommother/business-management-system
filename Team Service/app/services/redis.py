import json
import logging
from typing import Any, Optional, Dict, Union
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Подключение к Redis"""
        if self.redis is None:
            logger.info("Подключение к Redis...")
            try:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=int(settings.REDIS_PORT),
                    db=0,
                    decode_responses=True
                )
                # Проверка соединения
                await self.redis.ping()
                logger.info("Подключено к Redis")
            except Exception as e:
                logger.error(f"Ошибка подключения к Redis: {str(e)}")
                self.redis = None
                raise
    
    async def close(self):
        """Закрытие соединения с Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Отключено от Redis")
    
    async def set_key(self, key: str, value: Union[str, dict], expires_in: Optional[int] = None) -> bool:
        """Установка значения ключа в Redis"""
        if self.redis is None:
            await self.connect()
        
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            
            await self.redis.set(key, value)
            
            if expires_in:
                await self.redis.expire(key, expires_in)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка установки ключа Redis: {str(e)}")
            return False
    
    async def get_key(self, key: str) -> Optional[str]:
        """Получение значения ключа из Redis"""
        if self.redis is None:
            await self.connect()
        
        try:
            value = await self.redis.get(key)
            return value
        except Exception as e:
            logger.error(f"Ошибка получения ключа Redis: {str(e)}")
            return None
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Получение JSON значения из Redis"""
        value = await self.get_key(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON из ключа Redis: {key}")
        return None
    
    async def delete_key(self, key: str) -> bool:
        """Удаление ключа из Redis"""
        if self.redis is None:
            await self.connect()
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления ключа Redis: {str(e)}")
            return False
    
    async def cache_team(self, team_id: str, team_data: dict, expires_in: int = 3600):
        """Кэширование данных команды"""
        key = f"team:{team_id}"
        return await self.set_key(key, team_data, expires_in)
    
    async def get_cached_team(self, team_id: str) -> Optional[dict]:
        """Получение кэшированных данных команды"""
        key = f"team:{team_id}"
        return await self.get_json(key)
    
    async def invalidate_team_cache(self, team_id: str) -> bool:
        """Инвалидация всех кэшированных данных команды"""
        if self.redis is None:
            await self.connect()
        
        try:
            # Получение всех ключей для данной команды
            pattern = f"team:{team_id}*"
            cursor = 0
            keys_to_delete = []
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                keys_to_delete.extend(keys)
                
                if cursor == 0:
                    break
            
            # Удаление всех ключей
            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инвалидации кэша команды: {str(e)}")
            return False


# Создание синглтон-экземпляра
redis_service = RedisService()