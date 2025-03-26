from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel


class TeamMemberBase(BaseModel):
    user_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    role: str = "member"
    job_title: Optional[str] = None


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    role: Optional[str] = None
    job_title: Optional[str] = None
    is_active: Optional[bool] = None


class TeamMemberInDB(TeamMemberBase):
    id: uuid.UUID
    team_id: uuid.UUID
    joined_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TeamMemberResponse(TeamMemberInDB):
    pass


class TeamMemberWithUserInfo(TeamMemberResponse):
    user_name: str
    user_email: str


class CurrentTeamMember(BaseModel):
    """Информация о текущем пользователе в команде"""
    user_id: uuid.UUID
    team_id: uuid.UUID
    role: str
    is_active: bool

    class Config:
        orm_mode = True