from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
import uuid
from typing import List, Optional

from app.db.session import get_db
from app.db.crud import (
    get_team_news, create_team_news, update_team_news,
    delete_team_news, get_news_by_id, get_team_by_id,
    get_department_by_id, get_member_by_user_and_team
)
from app.schemas.news import (
    TeamNewsCreate, TeamNewsResponse, TeamNewsUpdate
)
from app.dependencies import get_team_member
from app.services.user_service import get_user_info
from app.db.models import MemberRole

router = APIRouter()


@router.post("/{team_id}/news", response_model=TeamNewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    team_id: uuid.UUID,
    news_data: TeamNewsCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Создание новости в команде"""
    # Проверка существования команды
    team = get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    # Проверка существования отдела, если указан
    if news_data.department_id:
        department = get_department_by_id(db, news_data.department_id)
        if not department or department.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный отдел не найден или не принадлежит данной команде"
            )
    
    # Проверка, что пользователь имеет права на публикацию новостей
    member = get_member_by_user_and_team(db, current_user_id, team_id)
    if member.role not in [MemberRole.ADMIN, MemberRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для публикации новостей"
        )
    
    # Создание новости
    news = create_team_news(db, team_id, news_data, current_user_id)
    
    # Получаем информацию о создателе новости
    creator_info = await get_user_info(current_user_id)
    creator_name = creator_info.get("name", "Неизвестно") if creator_info else "Неизвестно"
    
    news_response = TeamNewsResponse(
        **TeamNewsResponse.from_orm(news).dict(),
        creator_name=creator_name
    )
    
    # Публикация события создания новости
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_news_created,
        str(team_id),
        str(news.id),
        news.title
    )
    
    return news_response


@router.get("/{team_id}/news", response_model=List[TeamNewsResponse])
async def get_news_list(
    team_id: uuid.UUID,
    department_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Получение списка новостей команды"""
    # Проверка существования отдела, если указан
    if department_id:
        department = get_department_by_id(db, department_id)
        if not department or department.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный отдел не найден или не принадлежит данной команде"
            )
    
    # Получаем новости
    news_list = get_team_news(db, team_id, department_id, skip, limit)
    
    # Получаем информацию о создателях новостей
    result = []
    for news in news_list:
        creator_info = await get_user_info(news.created_by)
        creator_name = creator_info.get("name", "Неизвестно") if creator_info else "Неизвестно"
        
        news_response = TeamNewsResponse(
            **TeamNewsResponse.from_orm(news).dict(),
            creator_name=creator_name
        )
        result.append(news_response)
    
    return result


@router.get("/{team_id}/news/{news_id}", response_model=TeamNewsResponse)
async def get_news_details(
    team_id: uuid.UUID,
    news_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Получение детальной информации о новости"""
    # Получаем новость
    news = get_news_by_id(db, news_id)
    if not news or news.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Новость не найдена или не принадлежит указанной команде"
        )
    
    # Получаем информацию о создателе новости
    creator_info = await get_user_info(news.created_by)
    creator_name = creator_info.get("name", "Неизвестно") if creator_info else "Неизвестно"
    
    return TeamNewsResponse(
        **TeamNewsResponse.from_orm(news).dict(),
        creator_name=creator_name
    )


@router.patch("/{team_id}/news/{news_id}", response_model=TeamNewsResponse)
async def update_news_info(
    team_id: uuid.UUID,
    news_id: uuid.UUID,
    news_data: TeamNewsUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Обновление новости"""
    # Получаем новость
    news = get_news_by_id(db, news_id)
    if not news or news.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Новость не найдена или не принадлежит указанной команде"
        )
    
    # Проверка прав на редактирование новости
    member = get_member_by_user_and_team(db, current_user_id, team_id)
    if member.role != MemberRole.ADMIN and str(news.created_by) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для редактирования этой новости"
        )
    
    # Проверка существования отдела, если указан
    if news_data.department_id and news_data.department_id != news.department_id:
        department = get_department_by_id(db, news_data.department_id)
        if not department or department.team_id != team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный отдел не найден или не принадлежит данной команде"
            )
    
    # Обновляем новость
    updated_news = update_team_news(db, news_id, news_data)
    
    # Получаем информацию о создателе новости
    creator_info = await get_user_info(news.created_by)
    creator_name = creator_info.get("name", "Неизвестно") if creator_info else "Неизвестно"
    
    # Публикация события обновления новости
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_news_updated,
        str(team_id),
        str(news_id),
        updated_news.title
    )
    
    return TeamNewsResponse(
        **TeamNewsResponse.from_orm(updated_news).dict(),
        creator_name=creator_name
    )


@router.delete("/{team_id}/news/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_by_id(
    team_id: uuid.UUID,
    news_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_team_member())  # Проверка, что пользователь состоит в команде
):
    """Удаление новости"""
    # Получаем новость
    news = get_news_by_id(db, news_id)
    if not news or news.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Новость не найдена или не принадлежит указанной команде"
        )
    
    # Проверка прав на удаление новости
    member = get_member_by_user_and_team(db, current_user_id, team_id)
    if member.role != MemberRole.ADMIN and str(news.created_by) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этой новости"
        )
    
    # Удаляем новость
    success = delete_team_news(db, news_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить новость"
        )
    
    # Публикация события удаления новости
    from app.services.messaging import rabbitmq_service
    background_tasks.add_task(
        rabbitmq_service.publish_news_deleted,
        str(team_id),
        str(news_id)
    )
    
    return None