from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

# Base schema for any event payload
class EventPayloadBase(BaseModel):
    pass

# --- Task Service Events --- 

class TaskBasePayload(EventPayloadBase):
    task_id: int
    company_id: Optional[int] = None
    department_id: Optional[int] = None
    assignee_user_id: Optional[int] = None 

class TaskCreatedPayload(TaskBasePayload):
    title: str
    priority: Optional[str] = None
    created_at: datetime # Timestamp from the event source
    # Add other relevant fields from Task Service event

class TaskStatusChangedPayload(TaskBasePayload):
    old_status: str
    new_status: str
    changed_at: datetime # Timestamp from the event source
    # Optional: user_id who changed the status
    changed_by_user_id: Optional[int] = None 

class TaskPriorityChangedPayload(TaskBasePayload):
    old_priority: str
    new_priority: str
    changed_at: datetime

class TaskAssigneeChangedPayload(TaskBasePayload):
    old_assignee_user_id: Optional[int]
    new_assignee_user_id: Optional[int]
    changed_at: datetime

# --- User Service Events --- (Example structure)
# class UserCreatedPayload(EventPayloadBase):
#     user_id: int
#     email: str
#     company_id: int
#     department_id: int
#     registered_at: datetime

# ... Add schemas for other services (Company, Calendar) as needed

# Generic Event Structure (as received from RabbitMQ)
class Event(BaseModel):
    event_type: str # e.g., "task_created", "user_registered"
    payload: Dict[str, Any] # We'll validate this payload against specific schemas 