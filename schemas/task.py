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
    status: TaskStatus = TaskStatus.not_started  # updated to non-optional with default
    priority: PriorityLevel = PriorityLevel.medium  # updated to non-optional with default
    due_date: Optional[datetime] = None
    is_completed: bool = False
    estimated_time: Optional[float] = 0.25  
    actual_time: Optional[float] = 0.25  
    tags: List[str] = []  # updated to non-optional with default list
    dependency_ids: Optional[List[int]] = []

    class Config:
        orm_mode = True


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    is_completed: bool
    priority: PriorityLevel
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]  # updated to be Optional to match model
    estimated_time: Optional[float] = 0.25  
    actual_time: Optional[float] = 0.25  
    user_id: str
    tags: List[TagReadNested] = []
    dependencies: List[int] = []

    class Config:
        orm_mode = True
        model_config = {"from_attributes": True}


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    estimated_time: Optional[float] = 0.25  
    actual_time: Optional[float] = 0.25  
    priority: Optional[PriorityLevel] = None
    is_completed: Optional[bool] = None
    dependency_ids: Optional[List[int]] = None

    class Config:
        orm_mode = True
