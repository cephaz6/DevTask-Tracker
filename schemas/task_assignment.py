# schemas/task_assignment.py

from pydantic import BaseModel
from datetime import datetime
from typing import List 

class TaskAssignmentBase(BaseModel):
    task_id: str
    user_id: str
    is_watcher: bool = False  # False => assignee; True => watcher


class TaskWatcher(BaseModel):
    user_id: str
    is_watcher: bool = True  # Always True for watchers, False for assignees


class TaskAssignmentCreate(TaskAssignmentBase):
    pass


class TaskAssignmentRead(TaskAssignmentBase):
    id: str
    assigned_at: datetime

    class Config:
        orm_mode = True


class TaskAssignmentUpdatePayload(BaseModel):
    """Schema for updating task assignments."""
    user_ids: List[str] 
