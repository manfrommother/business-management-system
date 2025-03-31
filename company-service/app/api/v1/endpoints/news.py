# company-service/app/api/v1/endpoints/news.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Позже добавим зависимости
from app.db.session import get_db
# Импортируем зависимость для проверки компании
from .departments import get_company_or_404

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.News],
    summary="Получить список новостей компании",
    description="Возвращает список новостей для указанной компании (по умолчанию только активные и опубликованные).",
    # TODO: Права: участник компании
)
async def read_company_news(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    skip: int = 0,
    limit: int = 100,
    only_published: bool = Query(True, description="Показывать только опубликованные новости"),
    include_archived: bool = Query(False, description="Включить архивные новости в список"),
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить список новостей компании."""
    # TODO: Проверка прав
    news_list = crud.crud_news.get_multi_by_company(
        db=db,
        company_id=company.id,
        skip=skip,
        limit=limit,
        only_published=only_published,
        include_archived=include_archived
    )
    return news_list

@router.post(
    "/",
    response_model=schemas.News,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новость в компании",
    description="Публикует новую новость или создает черновик.",
    # TODO: Права: администратор компании или другая роль с правом публикации
)
async def create_news(
    *,
    db: Session = Depends(get_db),
    news_in: schemas.NewsCreate,
    company: models.Company = Depends(get_company_or_404),
    # current_user: models.User = Depends(deps.get_current_publisher(company_id)) # Пример
    current_user_id: int = 1 # ЗАГЛУШКА - ID автора
) -> Any:
    """
    Создать новость.
    - **title**: Заголовок (обязательно)
    - **content**: Содержание (обязательно)
    - **target_department_id**: ID отдела для таргетинга (опционально)
    - **media_attachments**: Список вложений (опционально)
    - **is_published**: Опубликовать сразу (по умолчанию True)
    - **published_at**: Время отложенной публикации (UTC, опционально)
    """
    # TODO: Проверка прав
    # TODO: Проверить существование target_department_id, если указан
    news = crud.crud_news.create_with_company(
        db=db,
        obj_in=news_in,
        company_id=company.id,
        author_user_id=current_user_id # ЗАГЛУШКА
    )
    return news

@router.get(
    "/{news_id}",
    response_model=schemas.News,
    summary="Получить информацию о новости",
    responses={404: {"description": "Новость не найдена"}},
    # TODO: Права: участник компании
)
async def read_news_item(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    news_id: int = Path(..., description="ID новости"),
    # current_user: models.User = Depends(deps.get_current_member(company_id)) # Пример
) -> Any:
    """Получить детальную информацию о новости по ID."""
    # TODO: Проверка прав
    news = crud.crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != company.id or news.is_archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")
    # TODO: Дополнительная проверка на is_published для обычных пользователей?
    return news

@router.put(
    "/{news_id}",
    response_model=schemas.News,
    summary="Обновить новость",
    responses={404: {"description": "Новость не найдена"}},
    # TODO: Права: автор новости или администратор компании
)
async def update_news_item(
    *,
    db: Session = Depends(get_db),
    news_in: schemas.NewsUpdate,
    company: models.Company = Depends(get_company_or_404),
    news_id: int = Path(..., description="ID новости"),
    # current_user: models.User = Depends(deps.get_news_editor(news_id)) # Пример
) -> Any:
    """
    Обновить информацию о новости.
    Передаются только изменяемые поля.
    """
    # TODO: Проверка прав
    news = crud.crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")
    updated_news = crud.crud_news.update(db=db, db_obj=news, obj_in=news_in)
    return updated_news

@router.delete(
    "/{news_id}",
    response_model=schemas.News,
    summary="Архивировать новость",
    responses={404: {"description": "Новость не найдена"}},
    # TODO: Права: автор новости или администратор компании
)
async def archive_news_item(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    news_id: int = Path(..., description="ID новости"),
    # current_user: models.User = Depends(deps.get_news_editor(news_id)) # Пример
) -> Any:
    """Архивировать (мягко удалить) новость."""
    # TODO: Проверка прав
    news = crud.crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")
    archived_news = crud.crud_news.archive(db=db, news_id=news_id)
    return archived_news

# Эндпоинт для разархивации (опционально)
@router.post(
    "/{news_id}/unarchive",
    response_model=schemas.News,
    summary="Восстановить новость из архива",
    responses={404: {"description": "Новость не найдена в архиве"}},
    # TODO: Права: администратор компании
)
async def unarchive_news_item(
    *,
    db: Session = Depends(get_db),
    company: models.Company = Depends(get_company_or_404),
    news_id: int = Path(..., description="ID новости"),
    # current_user: models.User = Depends(deps.get_current_company_admin(company_id)) # Пример
) -> Any:
    """Восстановить новость из архива."""
    # TODO: Проверка прав
    unarchived_news = crud.crud_news.unarchive(db=db, news_id=news_id)
    if not unarchived_news or unarchived_news.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Архивированная новость не найдена")
    return unarchived_news 