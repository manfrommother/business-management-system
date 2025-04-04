from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    head_user_id: Optional[uuid.UUID] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    head_user_id: Optional[uuid.UUID] = None


class DepartmentInDB(DepartmentBase):
    id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DepartmentResponse(DepartmentInDB):
    pass


class DepartmentTreeNode(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    head_user_id: Optional[uuid.UUID] = None
    children: List['DepartmentTreeNode'] = []

    class Config:
        orm_mode = True


# Рекурсивный тип
DepartmentTreeNode.update_forward_refs()


class OrganizationStructure(BaseModel):
    team_id: uuid.UUID
    team_name: str
    departments: List[DepartmentTreeNode] = []