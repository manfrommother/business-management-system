from typing import List, Any, Optional
import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


# === События ===

@router.get("/", response_model=List[schemas.Event])
async def read_events(
    calendar_id: int, # Получаем из пути /api/v1/calendars/{calendar_id}/events
    db: AsyncSession = Depends(deps.get_db),
    start_time: Optional[datetime.datetime] = Query(None, description="Start time for filtering events"),
    end_time: Optional[datetime.datetime] = Query(None, description="End time for filtering events"),
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Retrieve events for a specific calendar, optionally filtered by time range."""
    # Проверка доступа к календарю
    calendar = await crud.calendar.get(db=db, id=calendar_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")
    # TODO: Более сложная проверка прав (владелец календаря, участник команды/отдела)
    if calendar.owner_user_id != current_user_id and not calendar.is_team_calendar:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view this calendar")

    if start_time and end_time:
        events = await crud.event.get_multi_by_calendar_and_time_range(
            db,
            calendar_id=calendar_id,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit
        )
    else:
        events = await crud.event.get_multi_by_calendar(
            db, calendar_id=calendar_id, skip=skip, limit=limit
        )
    return events


@router.post("/", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    calendar_id: int,
    *,
    db: AsyncSession = Depends(deps.get_db),
    event_in: schemas.EventCreate,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Create new event in a specific calendar."""
    # Проверка доступа к календарю на запись
    calendar = await crud.calendar.get(db=db, id=calendar_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")
    if calendar.owner_user_id != current_user_id and not calendar.is_team_calendar:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create event in this calendar")

    # Создаем правило повторения, если оно передано
    recurring_pattern_id: Optional[int] = None
    if event_in.recurring_pattern:
        # TODO: Валидация дат в recurring_pattern (start_date >= event.start_time.date())
        created_pattern = await crud.recurring_pattern.create(db=db, obj_in=event_in.recurring_pattern)
        recurring_pattern_id = created_pattern.id

    # Подготовка данных для создания события
    # Используем exclude, чтобы убрать recurring_pattern из данных для Event
    event_data = event_in.model_dump(exclude={"recurring_pattern"})
    event_data["calendar_id"] = calendar_id
    event_data["creator_user_id"] = current_user_id
    event_data["recurring_pattern_id"] = recurring_pattern_id # Добавляем ID правила

    # Создание события с помощью CRUDBase (он ожидает словарь)
    # Нужно либо передать словарь, либо обновить CRUDBase.create
    # Пока создадим модель напрямую, чтобы использовать словарь
    db_event = models.Event(**event_data)
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    event = db_event # Переименуем для дальнейшего использования

    # Добавление участников, если они указаны
    if event_in.attendee_user_ids:
        await crud.event_attendee.add_attendees_to_event(
            db=db, event_id=event.id, user_ids=event_in.attendee_user_ids
        )
        await db.refresh(event)

    return event


@router.get("/{event_id}", response_model=schemas.Event)
async def read_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Get event by ID."""
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Проверка доступа к событию (через доступ к календарю)
    calendar = await crud.calendar.get(db=db, id=event.calendar_id)
    if not calendar:
         # Этого не должно произойти, если есть FK constraint
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Event calendar not found")
    # TODO: Более сложная проверка прав (владелец календаря, участник события, видимость)
    if calendar.owner_user_id != current_user_id and not calendar.is_team_calendar:
        # Дополнительно проверить видимость события и участие пользователя
        if event.visibility == schemas.EventVisibility.PRIVATE and event.creator_user_id != current_user_id:
             # Проверить, является ли пользователь участником
            attendee = await crud.event_attendee.get_by_event_and_user(db, event_id=event.id, user_id=current_user_id)
            if not attendee:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        elif event.visibility == schemas.EventVisibility.PARTICIPANTS_ONLY:
             attendee = await crud.event_attendee.get_by_event_and_user(db, event_id=event.id, user_id=current_user_id)
             if not attendee and event.creator_user_id != current_user_id:
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return event


@router.put("/{event_id}", response_model=schemas.Event)
async def update_event(
    event_id: int,
    *,
    db: AsyncSession = Depends(deps.get_db),
    event_in: schemas.EventUpdate,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Update an event."""
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # TODO: Проверка прав на обновление (создатель события, владелец календаря?)
    if event.creator_user_id != current_user_id:
        # Возможно, владелец календаря тоже может редактировать?
        calendar = await crud.calendar.get(db=db, id=event.calendar_id)
        if not calendar or calendar.owner_user_id != current_user_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    event = await crud.event.update(db=db, db_obj=event, obj_in=event_in)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> None:
    """Delete an event (soft delete)."""
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # TODO: Проверка прав на удаление (создатель, владелец календаря?)
    if event.creator_user_id != current_user_id:
        calendar = await crud.calendar.get(db=db, id=event.calendar_id)
        if not calendar or calendar.owner_user_id != current_user_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    await crud.event.delete_event(db=db, event_id=event_id)


@router.post("/{event_id}/restore", response_model=schemas.Event)
async def restore_event(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Restore a soft-deleted event."""
     # TODO: Проверка прав?
    restored_event = await crud.event.restore_event(db=db, event_id=event_id)
    if not restored_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found or not deleted")
    return restored_event


# === Участники ===

@router.get("/{event_id}/attendees", response_model=List[schemas.EventAttendee])
async def read_event_attendees(
    event_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Retrieve attendees for a specific event."""
    # Сначала проверяем доступ к самому событию
    await read_event(event_id=event_id, db=db, current_user_id=current_user_id)
    attendees = await crud.event_attendee.get_multi_by_event(db=db, event_id=event_id)
    return attendees


@router.post("/{event_id}/attendees", response_model=List[schemas.EventAttendee])
async def add_event_attendees(
    event_id: int,
    user_ids: List[int], # Передаем список ID в теле запроса или параметрах?
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Add attendees to an event."""
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    # TODO: Проверка прав на добавление участников (создатель, владелец календаря?)
    if event.creator_user_id != current_user_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    attendees = await crud.event_attendee.add_attendees_to_event(
        db=db, event_id=event_id, user_ids=user_ids
    )
    return attendees


@router.delete("/{event_id}/attendees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_event_attendee(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> None:
    """Remove an attendee from an event."""
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # TODO: Проверка прав (создатель события, владелец календаря, сам участник?)
    if event.creator_user_id != current_user_id and user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    deleted_attendee = await crud.event_attendee.remove_by_event_and_user(
        db=db, event_id=event_id, user_id=user_id
    )
    if not deleted_attendee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found")


@router.put("/{event_id}/attendees/{user_id}/status", response_model=schemas.EventAttendee)
async def update_attendee_status(
    event_id: int,
    user_id: int,
    status_in: schemas.EventAttendeeStatusUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Update the status of an attendee for an event."""
    # Проверка, что пользователь обновляет свой статус или является создателем
    event = await crud.event.get(db=db, id=event_id)
    if not event or event.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    if user_id != current_user_id:
        # TODO: Позволить создателю менять статус? Пока запрещено.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change status for another user")

    updated_attendee = await crud.event_attendee.update_status(
        db=db, event_id=event_id, user_id=user_id, status=status_in.status
    )
    if not updated_attendee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found")
    return updated_attendee 