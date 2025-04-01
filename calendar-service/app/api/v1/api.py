from fastapi import APIRouter

from app.api.v1.endpoints import calendars, events, settings, availability # Добавляем availability

api_router = APIRouter()

# Подключаем маршрутизатор для календарей
api_router.include_router(calendars.router, prefix="/calendars", tags=["calendars"])

# Подключаем маршрутизатор для событий (обратите внимание на вложенный путь)
api_router.include_router(events.router, prefix="/calendars/{calendar_id}/events", tags=["events-calendar"])
# Отдельный префикс для доступа к событиям напрямую по ID
api_router.include_router(events.router, prefix="/events", tags=["events-direct"])
# Отдельный префикс для участников (вложенный в события)
api_router.include_router(events.router, prefix="/events/{event_id}/attendees", tags=["event-attendees"])

# Подключаем маршрутизатор для настроек
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

# Подключаем маршрутизатор для availability
api_router.include_router(availability.router, prefix="/availability", tags=["availability"]) 