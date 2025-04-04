from pydantic import BaseModel, Json
from typing import Optional, Any
from datetime import datetime

# Base schema for common fields
class AnalyticsDataBase(BaseModel):
    metric_key: str
    metric_value: Json[Any]  # Use Json type for validation
    timestamp: datetime
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    user_id: Optional[int] = None
    task_id: Optional[int] = None
    # Add other dimensions if needed

# Schema for creating data (e.g., via API or event consumption)
class AnalyticsDataCreate(AnalyticsDataBase):
    pass  # Inherits all fields from base

# Schema for reading data (includes ID and timestamps from DB)
class AnalyticsData(AnalyticsDataBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic V2 uses this instead of orm_mode 