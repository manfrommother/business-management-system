# company-service/app/api/v1/endpoints/news.py

from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api import deps # Импортируем зависимости
from app.db.session import get_db
# Убираем get_company_or_404
# from .departments import get_company_or_404
# Импортируем CRUD напрямую
from app.crud import crud_news, crud_department
from app.models.membership import MembershipRole # Импортируем MembershipRole

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.News],
    summary="Получить список новостей компании",
    description="Возвращает список новостей для указанной компании.",
    responses={403: {"description": "Доступ запрещен"}},
)
async def read_company_news(
    *,
    # company_id из Path будет передан в get_current_member
    db: Session = Depends(get_db),
    membership: models.Membership = Depends(deps.get_current_member), # Проверяем членство
    skip: int = 0,
    limit: int = 100,
    only_published: bool = Query(True, description="Показывать только опубликованные новости"),
    include_archived: bool = Query(False, description="Включить архивные новости в список"),
) -> Any:
    """Получить список новостей компании (доступно участникам)."""
    # Права проверены
    news_list = crud_news.get_multi_by_company(
        db=db,
        company_id=membership.company_id,
        skip=skip,
        limit=limit,
        only_published=only_published, # Учитываем published_at <= now()
        include_archived=include_archived
    )
    return news_list

@router.post(
    "/",
    response_model=schemas.News,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новость в компании",
    description="Публикует новую новость или создает черновик.",
    responses={403: {"description": "Доступ запрещен (требуется админ/менеджер)"}},
)
async def create_news(
    *,
    # company_id из Path будет передан в get_current_company_manager
    db: Session = Depends(get_db),
    news_in: schemas.NewsCreate,
    # Требуем права менеджера или админа для публикации
    membership: models.Membership = Depends(deps.get_current_company_manager),
) -> Any:
    """
    Создать новость (доступно админам/менеджерам).
    - **title**: Заголовок (обязательно)
    - **content**: Содержание (обязательно)
    - **target_department_id**: ID отдела для таргетинга (опционально)
    - **media_attachments**: Список вложений (опционально)
    - **is_published**: Опубликовать сразу (по умолчанию True)
    - **published_at**: Время отложенной публикации (UTC, опционально)
    """
    # Права проверены
    company_id = membership.company_id
    current_user_id = membership.user_id # ID автора

    # Проверка target_department_id
    if news_in.target_department_id:
        target_dept = crud_department.get(db, department_id=news_in.target_department_id)
        if not target_dept or target_dept.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Целевой отдел с ID {news_in.target_department_id} не найден в этой компании."
            )

    news = crud_news.create_with_company(
        db=db,
        obj_in=news_in,
        company_id=company_id,
        author_user_id=current_user_id
    )
    return news

@router.get(
    "/{news_id}",
    response_model=schemas.News,
    summary="Получить информацию о новости",
    responses={
        404: {"description": "Новость не найдена"},
        403: {"description": "Доступ запрещен"}
    },
)
async def read_news_item(
    *,
    # company_id из Path будет передан в get_current_member
    db: Session = Depends(get_db),
    news_id: int = Path(..., description="ID новости"),
    membership: models.Membership = Depends(deps.get_current_member), # Проверяем членство
) -> Any:
    """Получить детальную информацию о новости (доступно участникам)."""
    # Права проверены
    news = crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")
    # TODO: Проверка is_published, published_at для не-админов/не-авторов?
    return news

@router.put(
    "/{news_id}",
    response_model=schemas.News,
    summary="Обновить новость",
    responses={
        404: {"description": "Новость не найдена"},
        403: {"description": "Доступ запрещен (требуется админ/менеджер или автор)"}
    },
)
async def update_news_item(
    *,
    # company_id из Path будет передан в get_current_company_manager_or_author
    # ЗАМЕНА ЗАВИСИМОСТИ! Нужна новая или проверка внутри.
    db: Session = Depends(get_db),
    news_in: schemas.NewsUpdate,
    news_id: int = Path(..., description="ID новости"),
    # Используем зависимость, которая требует членства, но права проверим ниже
    membership: models.Membership = Depends(deps.get_current_member),
) -> Any:
    """
    Обновить информацию о новости (доступно админам/менеджерам ИЛИ автору).
    Передаются только изменяемые поля.
    """
    news = crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")

    # Проверка прав: админ, менеджер ИЛИ автор
    is_admin_or_manager = membership.role in [MembershipRole.ADMIN, MembershipRole.MANAGER]
    is_author = news.author_user_id == membership.user_id

    if not (is_admin_or_manager or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на редактирование этой новости. Требуется роль админа/менеджера или авторство."
        )

    updated_news = crud_news.update(db=db, db_obj=news, obj_in=news_in)
    return updated_news

@router.delete(
    "/{news_id}",
    response_model=schemas.News,
    summary="Архивировать новость",
    responses={
        404: {"description": "Новость не найдена"},
        403: {"description": "Доступ запрещен (требуется админ/менеджер или автор)"}
    },
)
async def archive_news_item(
    *,
    # company_id из Path будет передан в get_current_company_manager_or_author
    # ЗАМЕНА ЗАВИСИМОСТИ! Нужна новая или проверка внутри.
    db: Session = Depends(get_db),
    news_id: int = Path(..., description="ID новости"),
    # Используем зависимость, которая требует членства, но права проверим ниже
    membership: models.Membership = Depends(deps.get_current_member),
) -> Any:
    """Архивировать (мягко удалить) новость (доступно админам/менеджерам ИЛИ автору)."""
    news = crud_news.get(db=db, news_id=news_id)
    if not news or news.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Новость не найдена")

    # Проверка прав: админ, менеджер ИЛИ автор
    is_admin_or_manager = membership.role in [MembershipRole.ADMIN, MembershipRole.MANAGER]
    is_author = news.author_user_id == membership.user_id

    if not (is_admin_or_manager or is_author):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав на архивирование этой новости. Требуется роль админа/менеджера или авторство."
        )

    archived_news = crud_news.archive(db=db, news_id=news_id)
    if not archived_news:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не удалось архивировать новость")
    return archived_news

@router.post(
    "/{news_id}/unarchive",
    response_model=schemas.News,
    summary="Восстановить новость из архива",
    responses={
        404: {"description": "Новость не найдена в архиве"},
        403: {"description": "Доступ запрещен (требуется админ/менеджер)"}
    },
)
async def unarchive_news_item(
    *,
    # company_id из Path будет передан в get_current_company_manager
    db: Session = Depends(get_db),
    news_id: int = Path(..., description="ID новости"),
    membership: models.Membership = Depends(deps.get_current_company_manager), # Проверяем права менеджера/админа
) -> Any:
    """Восстановить новость из архива (доступно админам/менеджерам)."""
    # Права проверены
    unarchived_news = crud_news.unarchive(db=db, news_id=news_id)
    if not unarchived_news or unarchived_news.company_id != membership.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Архивированная новость не найдена")
    return unarchived_news 