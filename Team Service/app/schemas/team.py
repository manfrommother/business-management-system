from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TeamInDB(TeamBase):
    id: uuid.UUID
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TeamResponse(TeamInDB):
    pass


class SimpleTeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        orm_mode = True


class TeamInviteBase(BaseModel):
    email: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    role: str = "member"
    expires_days: int = 7  # Срок действия в днях


class TeamInviteCreate(TeamInviteBase):
    pass


class TeamInviteResponse(BaseModel):
    id: uuid.UUID
    code: str
    team_id: uuid.UUID
    email: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    role: str
    expires_at: datetime
    is_used: bool
    created_at: datetime

    class Config:
        orm_mode = True


class TeamJoinRequest(BaseModel):
    code: str