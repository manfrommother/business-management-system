from typing import List, Optional
import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app import crud, models, schemas


class AvailabilityService:

    async def get_busy_slots(
        self,
        db: AsyncSession,
        user_ids: List[int],
        start_time: datetime.datetime,
        end_time: datetime.datetime
    ) -> List[schemas.BusySlot]:
        """Находит все события, пересекающиеся с заданным интервалом для списка пользователей."""

        busy_slots: List[schemas.BusySlot] = []

        # 1. Получить все календари, принадлежащие этим пользователям
        # (предполагаем, что проверяем только личные основные календари)
        # TODO: Уточнить, какие календари проверять (все личные, командные?)
        user_calendars = []
        for user_id in user_ids:
            # Ищем основной календарь пользователя
            primary_calendar = await crud.calendar.get_primary_calendar(db, owner_user_id=user_id)
            if primary_calendar:
                user_calendars.append(primary_calendar)
            else:
                # Если нет основного, возможно, стоит проверить все личные?
                # Или создать основной? Пока пропустим пользователя.
                pass

        if not user_calendars:
            return []

        calendar_ids = [cal.id for cal in user_calendars]
        owner_map = {cal.id: cal.owner_user_id for cal in user_calendars}

        # 2. Найти все события в этих календарях, пересекающиеся с интервалом
        # TODO: Учесть повторяющиеся события (потребуется генерация экземпляров)
        # TODO: Учесть часовые пояса пользователей и события (пока считаем все в UTC)
        # TODO: Учесть event_status (e.g., не учитывать CANCELLED)

        conflicting_events_result = await db.execute(
            select(models.Event)
            .where(models.Event.calendar_id.in_(calendar_ids))
            .where(models.Event.is_deleted == False)
            .where(models.Event.status != models.EventStatus.CANCELLED) # Исключаем отмененные
            .where(
                and_(
                    models.Event.start_time < end_time,
                    models.Event.end_time > start_time
                )
            )
        )
        conflicting_events = conflicting_events_result.scalars().all()

        # 3. Преобразовать найденные события в BusySlot
        for event in conflicting_events:
            busy_slots.append(
                schemas.BusySlot(
                    user_id=owner_map[event.calendar_id],
                    start_time=event.start_time,
                    end_time=event.end_time,
                    event_id=event.id,
                    event_title=event.title
                )
            )

        # TODO: Добавить "заблокированные" слоты из настроек (рабочие часы)

        return busy_slots

    async def find_available_slots(
        self,
        db: AsyncSession,
        user_ids: List[int],
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        duration_minutes: int
    ) -> List[schemas.TimeSuggestion]:
        """Находит свободные слоты достаточной длительности для всех пользователей."""

        # 1. Получить все занятые слоты для всех пользователей в заданном интервале
        all_busy_slots = await self.get_busy_slots(db, user_ids, start_time, end_time)

        # 2. Сгруппировать занятые слоты по пользователям
        user_busy_map: dict[int, List[schemas.BusySlot]] = {user_id: [] for user_id in user_ids}
        for slot in all_busy_slots:
            if slot.user_id in user_busy_map:
                user_busy_map[slot.user_id].append(slot)

        # 3. Для каждого пользователя найти его свободные интервалы
        # TODO: Реализовать алгоритм поиска свободных слотов
        # (пройти по временной шкале от start_time до end_time,
        # учитывая занятые слоты и рабочие часы/настройки)

        # 4. Найти пересечение свободных интервалов для всех пользователей
        # TODO: Реализовать алгоритм пересечения интервалов

        # 5. Отфильтровать пересекающиеся свободные интервалы по длительности
        # TODO: Реализовать фильтрацию по duration_minutes

        # Заглушка - возвращаем пустой список
        suggestions: List[schemas.TimeSuggestion] = []
        return suggestions


availability_service = AvailabilityService() 