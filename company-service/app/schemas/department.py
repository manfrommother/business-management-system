# company-service/app/schemas/department.py

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# Базовая схема для Департамента
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=255, description="Название подразделения")
    parent_department_id: Optional[int] = Field(None, description="ID родительского подразделения (для иерархии)")
    manager_user_id: Optional[int] = Field(None, description="ID руководителя (из User Service)")

# Схема для создания нового Департамента
class DepartmentCreate(DepartmentBase):
    # company_id будет браться из пути URL, а не из тела запроса
    pass

# Схема для обновления Департамента
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Название подразделения")
    parent_department_id: Optional[int] = Field(None, description="ID родительского подразделения")
    manager_user_id: Optional[int] = Field(None, description="ID руководителя")
    is_archived: Optional[bool] = Field(None, description="Архивировать/разархивировать подразделение")

# Схема для возврата данных о Департаменте из API
class Department(DepartmentBase):
    id: int = Field(..., description="Уникальный идентификатор подразделения")
    company_id: int = Field(..., description="ID компании, к которой относится подразделение")
    is_archived: bool = Field(..., description="Флаг архивации")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления")

    # Опционально: можно добавить сюда информацию о дочерних отделах или руководителях
    # child_departments: List['Department'] = [] # Пример рекурсивной схемы

    model_config = {"from_attributes": True}

# Рекурсивная схема для отображения иерархии (если нужно)
# Department.model_rebuild() # Обновляем ссылки после определения 