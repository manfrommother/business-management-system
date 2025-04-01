from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.api import deps
from app.services.availability_service import availability_service # Импортируем сервис
from app import crud # Нужен для блокировки времени

router = APIRouter()


@router.post("/check", response_model=schemas.AvailabilityResponse)
async def check_availability(
    query: schemas.AvailabilityQuery,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Check busy slots for a list of users within a given time range."""
    # TODO: Проверка прав? Должен ли пользователь иметь право видеть занятость других?
    busy_slots = await availability_service.get_busy_slots(
        db=db,
        user_ids=query.user_ids,
        start_time=query.start_time,
        end_time=query.end_time
    )
    return schemas.AvailabilityResponse(busy_slots=busy_slots)


@router.post("/suggestions", response_model=schemas.SuggestionResponse)
async def get_availability_suggestions(
    query: schemas.SuggestionQuery,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Suggest available time slots for a meeting."""
    # TODO: Проверка прав?
    suggestions = await availability_service.find_available_slots(
        db=db,
        user_ids=query.user_ids,
        start_time=query.start_time,
        end_time=query.end_time,
        duration_minutes=query.duration_minutes
    )
    # Пока возвращает пустой список, т.к. логика не реализована
    return schemas.SuggestionResponse(suggestions=suggestions)


@router.post("/block", response_model=schemas.Event)
async def block_time_in_calendar(
    query: schemas.BlockTimeQuery,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Block a time slot in the user's calendar."""
    calendar_id_to_use = query.calendar_id
    if not calendar_id_to_use:
        # Если ID календаря не указан, ищем основной календарь пользователя
        primary_calendar = await crud.calendar.get_primary_calendar(db, owner_user_id=current_user_id)
        if not primary_calendar:
            # TODO: Если нет основного, создать его или вернуть ошибку?
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Primary calendar not found for the user. Please specify calendar_id."
            )
        calendar_id_to_use = primary_calendar.id
    else:
        # Проверяем, что указанный календарь принадлежит пользователю
        calendar = await crud.calendar.get(db=db, id=calendar_id_to_use)
        if not calendar or calendar.owner_user_id != current_user_id or calendar.is_team_calendar:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN,
                 detail="Cannot block time in the specified calendar."
             )

    # Создаем событие типа TIME_BLOCK
    event_in = schemas.EventCreate(
        calendar_id=calendar_id_to_use,
        creator_user_id=current_user_id,
        title=query.title,
        start_time=query.start_time,
        end_time=query.end_time,
        event_type=schemas.EventType.TIME_BLOCK,
        visibility=schemas.EventVisibility.PRIVATE # Заблокированное время обычно приватное
    )
    blocked_event = await crud.event.create(db=db, obj_in=event_in)
    return blocked_event 