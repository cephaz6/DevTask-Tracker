from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from schemas.tag import TagReadNested
from enum import Enum

class TaskStatus(str, Enum):
    """Enumeration for task status."""
    not_started = "not_started"
    pending = "pending"
    in_progress = "in_progress"
    on_hold = "on_hold"
    cancelled = "cancelled"
    completed = "completed"

class PriorityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.pending
    priority: Optional[PriorityLevel] = PriorityLevel.medium
    due_date: Optional[datetime] = None
    is_completed: bool = False
    tags: Optional[List[str]] = []

    class Config:
        orm_mode = True 

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    is_completed: bool
    priority: Optional[PriorityLevel]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user_id: str 
    tags: List[TagReadNested] = []

    class Config:
        model_config = {"from_attributes": True}
        orm_mode = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    priority: Optional[PriorityLevel] = None
    is_completed: Optional[bool] = None 

    class Config:
        orm_mode = True