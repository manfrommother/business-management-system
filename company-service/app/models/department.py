from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

class Department(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    is_archived = Column(Boolean, default=False) # Для архивации подразделений

    # Внешний ключ к компании
    company_id = Column(Integer, ForeignKey("companys.id"), nullable=False)
    # Внешний ключ для иерархии (ссылка на родительский отдел)
    parent_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # ID руководителя (из User Service)
    manager_user_id = Column(Integer, nullable=True) # Nullable, если руководитель не назначен

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    company = relationship("Company", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], back_populates="child_departments")
    child_departments = relationship("Department", back_populates="parent_department", cascade="all, delete-orphan")

    # Связь с членством (сотрудниками отдела)
    # Потребуется добавить department_id в модель Membership
    memberships = relationship("Membership", back_populates="department") 