from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base schema for Metric
class MetricBase(BaseModel):
    name: str
    description: Optional[str] = None
    calculation_logic: Optional[str] = None
    aggregation_level: Optional[str] = None # e.g., 'company', 'department', 'user', 'task'
    granularity: Optional[str] = None # e.g., 'daily', 'weekly', 'monthly'

# Schema for creating a Metric
class MetricCreate(MetricBase):
    pass

# Schema for updating a Metric
class MetricUpdate(MetricBase):
    # Allow partial updates
    name: Optional[str] = None
    description: Optional[str] = None
    calculation_logic: Optional[str] = None
    aggregation_level: Optional[str] = None
    granularity: Optional[str] = None

# Schema for reading a Metric (includes DB fields)
class Metric(MetricBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 