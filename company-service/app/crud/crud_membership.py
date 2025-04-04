# company-service/app/crud/crud_membership.py

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.membership import Membership, MembershipStatus
from app.schemas.membership import MembershipCreate, MembershipUpdate

class CRUDMembership:
    def get(self, db: Session, membership_id: int) -> Optional[Membership]:
        """Получить членство по его ID."""
        return db.query(Membership).filter(Membership.id == membership_id).first()

    def get_by_user_and_company(
        self, db: Session, *, user_id: int, company_id: int
    ) -> Optional[Membership]:
        """Получить членство конкретного пользователя в конкретной компании."""
        return db.query(Membership).filter(
            Membership.company_id == company_id,
            Membership.user_id == user_id
        ).first()

    def get_multi_by_company(
        self, db: Session, *, company_id: int, skip: int = 0, limit: int = 100,
        include_inactive: bool = False
    ) -> List[Membership]:
        """Получить список членств для компании."""
        query = db.query(Membership).filter(Membership.company_id == company_id)
        if not include_inactive:
            query = query.filter(Membership.status == MembershipStatus.ACTIVE)
        return query.offset(skip).limit(limit).all()

    def get_multi_by_department(
        self, db: Session, *, department_id: int, skip: int = 0, limit: int = 100,
        include_inactive: bool = False
    ) -> List[Membership]:
        """Получить список членств для департамента."""
        query = db.query(Membership).filter(Membership.department_id == department_id)
        if not include_inactive:
            query = query.filter(Membership.status == MembershipStatus.ACTIVE)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: MembershipCreate, company_id: int) -> Membership:
        """
        Создать новую запись о членстве.
        Предполагается, что проверка на уникальность (user_id, company_id)
        уже сделана или обрабатывается на уровне БД.
        """
        db_obj = Membership(
            **obj_in.model_dump(),
            company_id=company_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Membership, obj_in: MembershipUpdate
    ) -> Membership:
        """Обновить данные о членстве (роль, отдел, статус)."""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_by_user_and_company(
        self, db: Session, *, user_id: int, company_id: int
    ) -> Optional[Membership]:
        """
        Деактивировать (мягко удалить) членство пользователя в компании.
        Возвращает удаленный объект или None, если не найден.
        """
        db_obj = self.get_by_user_and_company(db=db, user_id=user_id, company_id=company_id)
        if db_obj:
            # Вместо удаления меняем статус
            db_obj.status = MembershipStatus.INACTIVE
            # Можно также обнулить department_id или добавить leave_date
            # db_obj.department_id = None
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    # Можно добавить метод для полного удаления, если требуется
    # def remove(self, db: Session, *, id: int) -> Membership: ...


# Экземпляр CRUD для Membership
crud_membership = CRUDMembership() 