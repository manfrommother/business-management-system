# company-service/app/crud/crud_company.py

from typing import List, Optional, Type
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.company import Company, CompanyStatus
from app.schemas.company import CompanyCreate, CompanyUpdate

# Базовый CRUD класс (можно вынести в отдельный файл app/crud/base.py)
# чтобы переиспользовать для других моделей
class CRUDBase:
    def __init__(self, model: Type[Company]): # Используем Company как тип по умолчанию
        """
        Базовый CRUD класс с методами по умолчанию: Create, Read, Update, Delete.

        **Параметры**

        * `model`: Модель SQLAlchemy
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[Company]:
        return db.query(self.model).filter(self.model.id == id, self.model.is_deleted == False).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Company]:
        return db.query(self.model).filter(self.model.is_deleted == False).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CompanyCreate) -> Company:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Company, obj_in: CompanyUpdate
    ) -> Company:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db_obj.updated_at = datetime.utcnow() # Обновляем время вручную, если onupdate не используется или не подходит
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[Company]:
        """Мягкое удаление"""
        obj = db.query(self.model).get(id)
        if obj:
            obj.is_deleted = True
            obj.deleted_at = datetime.utcnow()
            obj.status = CompanyStatus.INACTIVE # Меняем статус при удалении
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj

    def restore(self, db: Session, *, id: int) -> Optional[Company]:
        """Восстановление после мягкого удаления"""
        obj = db.query(self.model).filter(self.model.id == id, self.model.is_deleted == True).first()
        if obj:
            obj.is_deleted = False
            obj.deleted_at = None
            obj.status = CompanyStatus.ACTIVE # Возвращаем активный статус
            obj.updated_at = datetime.utcnow()
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


# Создаем экземпляр CRUD для модели Company
crud_company = CRUDBase(Company) 