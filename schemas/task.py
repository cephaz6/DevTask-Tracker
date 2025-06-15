# In your server's schemas/task.py

from typing import Optional, List
from pydantic import BaseModel, Field, model_validator # Import model_validator
from datetime import datetime
from schemas.tag import TagReadNested
from enum import Enum
from schemas.comment import TaskCommentSummary
from schemas.user import UserReadMinimal
from schemas.task_assignment import TaskWatcher
from typing import ClassVar # Import ClassVar for internal fields


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
    status: TaskStatus = TaskStatus.not_started
    priority: PriorityLevel = PriorityLevel.medium
    due_date: Optional[datetime] = None
    is_completed: bool = False # Retain for explicit input, but will be overridden by status
    estimated_time: Optional[float] = 0.25
    actual_time: Optional[float] = 0.25
    tags: List[str] = []
    dependency_ids: Optional[List[str]] = []
    project_id: Optional[str] = None

    class Config:
        orm_mode = True
        model_config = {"from_attributes": True} # Added for Pydantic V2 compatibility

    # Validator to set is_completed based on status
    @model_validator(mode='after')
    def set_is_completed_from_status(self):
        if self.status == TaskStatus.completed:
            self.is_completed = True
        else:
            self.is_completed = False # Explicitly set to False if not completed
        return self


class TaskSummary(BaseModel):
    id: str
    title: str
    status: str

    class Config:
        orm_mode = True
        model_config = {"from_attributes": True}


class TaskRead(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    is_completed: bool # This will be consistent with 'status' due to backend validation
    priority: PriorityLevel
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    estimated_time: Optional[float]
    actual_time: Optional[float]
    user_id: str
    project_id: Optional[str] = None
    tags: List[TagReadNested] = []
    dependencies: List[TaskSummary] = []
    comments: List[TaskCommentSummary] = []
    assignments: List[TaskWatcher] = []
    user: Optional[UserReadMinimal] = Field(alias="owner")

    class Config:
        orm_mode = True
        model_config = {"from_attributes": True}
        populate_by_name = True
        allow_population_by_field_name = True


TaskRead.model_rebuild()


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None # Allow updating status
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None
    estimated_time: Optional[float] = None
    actual_time: Optional[float] = None
    priority: Optional[PriorityLevel] = None
    is_completed: Optional[bool] = None # Will be overridden if status is provided
    dependency_ids: Optional[List[str]] = None
    project_id: Optional[str] = None

    class Config:
        orm_mode = True
        model_config = {"from_attributes": True}

    # Validator to set is_completed based on status during update
    @model_validator(mode='after')
    def set_is_completed_from_status_update(self):
        # Only apply this logic if status is explicitly being updated
        if self.status is not None:
            self.is_completed = (self.status == TaskStatus.completed)
        # If status is not provided in the update, keep the existing is_completed value
        return self

