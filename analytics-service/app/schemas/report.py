from pydantic import BaseModel, Json
from typing import Optional, Dict, Any
from datetime import datetime

# Base schema for Report
class ReportBase(BaseModel):
    name: str
    type: str
    parameters: Optional[Dict[str, Any]] = None
    requested_by_user_id: int
    company_id: Optional[int] = None

# Schema for creating a Report request
class ReportCreate(ReportBase):
    pass

# Schema for updating a Report (e.g., status, result URL)
class ReportUpdate(BaseModel):
    status: Optional[str] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

# Schema for reading a Report (includes DB fields)
class Report(ReportBase):
    id: int
    status: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True 