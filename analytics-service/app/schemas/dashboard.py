from pydantic import BaseModel, Json
from typing import Optional, Dict, Any
from datetime import datetime

# Base schema for Dashboard
class DashboardBase(BaseModel):
    name: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = {}
    owner_id: int # Assuming owner is required

# Schema for creating a Dashboard
class DashboardCreate(DashboardBase):
    pass

# Schema for updating a Dashboard
class DashboardUpdate(BaseModel):
    # Allow partial updates
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    # owner_id typically shouldn't be updated directly here

# Schema for reading a Dashboard (includes DB fields)
class Dashboard(DashboardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 