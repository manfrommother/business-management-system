from datetime import datetime, timedelta
import uuid
from sqlalchemy import String, Boolean, Column, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deletion_date = Column(DateTime, nullable=True)
    email_veridied = Column(Boolean, default=True)
    role = Column(String, default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def mark_deleted(self):
        '''Отмечает пользователя как удаленного'''
        self.is_deleted = True
        self.is_active = False
        self.deletion_date = datetime.utcnow

    def restore(self):
        '''Восстанавливает пользователя, если прошло не более 30 дней'''
        if self.is_deleted and (datetime.utcnow() - self.deletion_date) <= timedelta(days=30):
            self.is_deleted = False
            self.is_active = True
            self.deletion_date = None
            return True
        return False
    

class VerificationToken(Base):
    __tablename__ = 'verification_tokens'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String, nullable=False, index=True)
    type = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def is_expired(self):
        '''Проверяет, истек ли срок действия токена'''
        return datetime.utcnow() > self.expires_at
