# company-service/app/crud/crud_news.py

from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc # Для сортировки по дате

from app.models.news import News
from app.schemas.news import NewsCreate, NewsUpdate

class CRUDNews:
    def get(self, db: Session, news_id: int) -> Optional[News]:
        """Получить новость по ID."""
        return db.query(News).filter(News.id == news_id, News.is_archived == False).first()

    def get_multi_by_company(
        self,
        db: Session,
        *,
        company_id: int,
        skip: int = 0,
        limit: int = 100,
        only_published: bool = True, # По умолчанию только опубликованные
        include_archived: bool = False # По умолчанию только неархивные
    ) -> List[News]:
        """Получить список новостей для компании."""
        query = db.query(News).filter(News.company_id == company_id)

        if not include_archived:
            query = query.filter(News.is_archived == False)

        if only_published:
            # Показываем опубликованные и те, что должны были опубликоваться
            now_aware = datetime.now(timezone.utc)
            query = query.filter(
                News.is_published == True,
                (News.published_at == None) | (News.published_at <= now_aware)
            )

        # Сортируем по дате публикации/создания (сначала новые)
        query = query.order_by(desc(News.published_at), desc(News.created_at))

        return query.offset(skip).limit(limit).all()

    def create_with_company(
        self, db: Session, *, obj_in: NewsCreate, company_id: int, author_user_id: Optional[int] = None
    ) -> News:
        """Создать новость для компании."""
        # Если время публикации не указано и is_published=True, ставим текущее время
        published_at = obj_in.published_at
        if published_at is None and obj_in.is_published:
            published_at = datetime.now(timezone.utc)
        elif published_at and published_at.tzinfo is None:
            # Считаем naive datetime как UTC
            published_at = published_at.replace(tzinfo=timezone.utc)


        db_obj = News(
            **obj_in.model_dump(exclude={"published_at"}),
            company_id=company_id,
            author_user_id=author_user_id,
            published_at=published_at
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: News, obj_in: NewsUpdate
    ) -> News:
        """Обновить новость."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Особая обработка published_at, если оно меняется
        if "published_at" in update_data and update_data["published_at"] is not None:
             published_at = update_data["published_at"]
             if published_at.tzinfo is None:
                 update_data["published_at"] = published_at.replace(tzinfo=timezone.utc)
        elif "published_at" in update_data and update_data["published_at"] is None:
             # Если сбрасываем время публикации, но новость опубликована
             if update_data.get("is_published", db_obj.is_published):
                 update_data["published_at"] = datetime.now(timezone.utc)


        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def archive(self, db: Session, *, news_id: int) -> Optional[News]:
        """Архивировать новость."""
        db_obj = self.get(db=db, news_id=news_id)
        if db_obj:
            db_obj.is_archived = True
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def unarchive(self, db: Session, *, news_id: int) -> Optional[News]:
        """Разархивировать новость."""
        db_obj = db.query(News).filter(News.id == news_id, News.is_archived == True).first()
        if db_obj:
            db_obj.is_archived = False
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

# Экземпляр CRUD для News
crud_news = CRUDNews() 