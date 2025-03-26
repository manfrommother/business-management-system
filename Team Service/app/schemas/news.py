from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel


class TeamNewsBase(BaseModel):
    title: str
    content: str
    department_id: Optional[uuid.UUID] = None
    is_pinned: bool = False


class TeamNewsCreate(TeamNewsBase):
    pass


class TeamNewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    is_pinned: Optional[bool] = None


class TeamNewsInDB(TeamNewsBase):
    id: uuid.UUID
    team_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TeamNewsResponse(TeamNewsInDB):
    creator_name: Optional[str] = None  # Имя создателя новости