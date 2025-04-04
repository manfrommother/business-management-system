from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Calendar])
async def read_calendars(
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Retrieve calendars owned by the current user."""
    # В реальном приложении здесь может быть логика получения и командных календарей
    calendars = await crud.calendar.get_by_owner(db, owner_user_id=current_user_id)
    # TODO: Добавить пагинацию, если get_by_owner будет ее поддерживать
    return calendars


@router.post("/", response_model=schemas.Calendar, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    *,
    db: AsyncSession = Depends(deps.get_db),
    calendar_in: schemas.CalendarCreate,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Create new calendar for the current user."""
    # Устанавливаем владельца календаря
    if not calendar_in.is_team_calendar:
        calendar_in.owner_user_id = current_user_id
    else:
        # TODO: Добавить проверку прав на создание командного календаря
        if not calendar_in.team_id and not calendar_in.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team ID or Department ID must be provided for team calendars."
            )
        # Проверка, что пользователь может создавать календарь для этой команды/отдела
        pass

    calendar = await crud.calendar.create(db=db, obj_in=calendar_in)
    # TODO: Возможно, нужно сделать созданный личный календарь primary по умолчанию?
    return calendar


@router.get("/{calendar_id}", response_model=schemas.Calendar)
async def read_calendar(
    *,
    db: AsyncSession = Depends(deps.get_db),
    calendar_id: int,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Get calendar by ID."""
    calendar = await crud.calendar.get(db=db, id=calendar_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")
    # TODO: Проверка прав доступа (владелец, участник команды/отдела)
    # if calendar.owner_user_id != current_user_id and not is_user_in_team(calendar.team_id...):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return calendar


@router.put("/{calendar_id}", response_model=schemas.Calendar)
async def update_calendar(
    *,
    db: AsyncSession = Depends(deps.get_db),
    calendar_id: int,
    calendar_in: schemas.CalendarUpdate,
    current_user_id: int = Depends(deps.get_current_user)
) -> Any:
    """Update a calendar."""
    calendar = await crud.calendar.get(db=db, id=calendar_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")
    # TODO: Проверка прав доступа (владелец)
    if calendar.owner_user_id != current_user_id and not calendar.is_team_calendar:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    # TODO: Добавить проверку прав на редактирование командных календарей

    calendar = await crud.calendar.update(db=db, db_obj=calendar, obj_in=calendar_in)
    return calendar


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    *,
    db: AsyncSession = Depends(deps.get_db),
    calendar_id: int,
    current_user_id: int = Depends(deps.get_current_user)
) -> None:
    """Delete a calendar."""
    calendar = await crud.calendar.get(db=db, id=calendar_id)
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")
    # TODO: Проверка прав доступа (владелец)
    if calendar.owner_user_id != current_user_id and not calendar.is_team_calendar:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    # TODO: Добавить проверку прав на удаление командных календарей
    # TODO: Что делать с событиями в удаляемом календаре? (мягкое удаление? каскадное?)

    await crud.calendar.remove(db=db, id=calendar_id)
    # Возвращаем None со статусом 204 