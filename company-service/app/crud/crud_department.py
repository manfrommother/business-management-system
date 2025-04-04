# company-service/app/crud/crud_department.py

from typing import List, Optional, Type

from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate

# Используем или наследуем CRUDBase, если он вынесен
# Пока создадим специфичный CRUD для Department

class CRUDDepartment:
    def get(self, db: Session, department_id: int) -> Optional[Department]:
        """Получить департамент по ID."""
        return db.query(Department).filter(Department.id == department_id, Department.is_archived == False).first()

    def get_multi_by_company(
        self, db: Session, *, company_id: int, skip: int = 0, limit: int = 100
    ) -> List[Department]:
        """Получить список активных департаментов для компании."""
        return (
            db.query(Department)
            .filter(Department.company_id == company_id, Department.is_archived == False)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_with_company(
        self, db: Session, *, obj_in: DepartmentCreate, company_id: int
    ) -> Department:
        """Создать новый департамент, привязанный к компании."""
        db_obj = Department(**obj_in.model_dump(), company_id=company_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Department, obj_in: DepartmentUpdate
    ) -> Department:
        """Обновить департамент."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        # Не обновляем updated_at вручную, т.к. в модели есть onupdate=func.now()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def archive(self, db: Session, *, department_id: int) -> Optional[Department]:
        """Архивировать департамент (мягкое удаление)."""
        db_obj = self.get(db=db, department_id=department_id)
        if db_obj:
            db_obj.is_archived = True
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def unarchive(self, db: Session, *, department_id: int) -> Optional[Department]:
        """Восстановить департамент из архива."""
        db_obj = db.query(Department).filter(Department.id == department_id, Department.is_archived == True).first()
        if db_obj:
            db_obj.is_archived = False
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    # TODO: Добавить функции для управления руководителями, перемещения сотрудников (возможно, в crud_membership)

# Экземпляр CRUD для Department
crud_department = CRUDDepartment() 