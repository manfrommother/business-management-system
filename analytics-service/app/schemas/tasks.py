from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

# --- Schemas for Task Analytics API Responses ---

class TasksByStatusResponse(BaseModel):
    status_counts: Dict[str, int]

class TaskSummaryResponse(BaseModel):
    total_tasks: int
    active_tasks: int # Example: count of tasks not 'completed' or 'cancelled'
    overdue_tasks: int # Need logic to determine this

class TaskCompletionTimeStats(BaseModel):
    average_completion_time_hours: Optional[float] = None
    median_completion_time_hours: Optional[float] = None
    # Could add stats by priority, type etc.

# Potentially add more response schemas for other task endpoints 