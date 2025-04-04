import httpx
import logging
from typing import Optional, Dict, Any
import uuid

from app.config import settings

logger = logging.getLogger(__name__)


async def get_user_info(user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Получение информации о пользователе из User Service"""
    url = f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Пользователь с ID {user_id} не найден в User Service")
                return None
            else:
                logger.error(f"Ошибка получения данных пользователя: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Ошибка при обращении к User Service: {str(e)}")
        return None


async def get_users_by_ids(user_ids: list[uuid.UUID]) -> Dict[str, Dict[str, Any]]:
    """Получение информации о нескольких пользователях по их ID"""
    url = f"{settings.USER_SERVICE_URL}/api/v1/users/batch"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"user_ids": [str(uid) for uid in user_ids]}
            )
            
            if response.status_code == 200:
                return {str(user['id']): user for user in response.json()}
            else:
                logger.error(f"Ошибка получения данных пользователей: {response.status_code} - {response.text}")
                return {}
    except Exception as e:
        logger.error(f"Ошибка при обращении к User Service: {str(e)}")
        return {}


async def verify_user_exists(user_id: uuid.UUID) -> bool:
    """Проверка существования пользователя в User Service"""
    user_info = await get_user_info(user_id)
    return user_info is not None


async def get_user_email(user_id: uuid.UUID) -> Optional[str]:
    """Получение email пользователя"""
    user_info = await get_user_info(user_id)
    if user_info:
        return user_info.get("email")
    return None