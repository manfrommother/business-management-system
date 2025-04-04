# company-service/app/crud/crud_invitation.py

import secrets
import string
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.invitation import Invitation, InvitationStatus
from app.schemas.invitation import InvitationCreate

# Генерация случайного кода приглашения
def generate_invitation_code(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

class CRUDInvitation:
    def get(self, db: Session, invitation_id: int) -> Optional[Invitation]:
        """Получить приглашение по ID."""
        return db.query(Invitation).filter(Invitation.id == invitation_id).first()

    def get_by_code(self, db: Session, *, code: str) -> Optional[Invitation]:
        """Получить приглашение по его уникальному коду."""
        return db.query(Invitation).filter(Invitation.code == code).first()

    def create_with_company(
        self, db: Session, *, obj_in: InvitationCreate, company_id: int, created_by_user_id: Optional[int] = None
    ) -> Invitation:
        """Создать новое приглашение для компании."""
        # Генерируем уникальный код
        while True:
            code = generate_invitation_code()
            if not self.get_by_code(db=db, code=code):
                break

        # Устанавливаем срок действия по умолчанию, если не задан (например, 7 дней)
        expires_at = obj_in.expires_at
        if expires_at is None:
             # Убедимся, что работаем с offset-aware datetime
            now_aware = datetime.now(timezone.utc)
            expires_at = now_aware + timedelta(days=7)
        elif expires_at.tzinfo is None:
             # Если передан naive datetime, считаем его UTC
             expires_at = expires_at.replace(tzinfo=timezone.utc)


        db_obj = Invitation(
            **obj_in.model_dump(exclude={"expires_at"}), # Исключаем expires_at, т.к. обработали его
            code=code,
            company_id=company_id,
            created_by_user_id=created_by_user_id,
            expires_at=expires_at # Устанавливаем обработанное значение
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self, db: Session, *, db_obj: Invitation, status: InvitationStatus
    ) -> Invitation:
        """Обновить статус приглашения."""
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def increment_usage(self, db: Session, *, db_obj: Invitation) -> Invitation:
        """Увеличить счетчик использований приглашения."""
        db_obj.times_used += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def count_pending_by_company(self, db: Session, *, company_id: int) -> int:
        """Подсчитать количество ожидающих приглашений для компании."""
        # Также учитываем срок действия
        now_aware = datetime.now(timezone.utc)
        return db.query(Invitation).filter(
            Invitation.company_id == company_id,
            Invitation.status == InvitationStatus.PENDING,
            (Invitation.expires_at == None) | (Invitation.expires_at > now_aware),
            (Invitation.usage_limit == None) | (Invitation.times_used < Invitation.usage_limit)
        ).count()

    # TODO: Методы для отзыва (revoke), возможно, листинга приглашений

# Экземпляр CRUD для Invitation
crud_invitation = CRUDInvitation() 