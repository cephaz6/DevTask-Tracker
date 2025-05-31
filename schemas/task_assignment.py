# schemas/task_assignment.py

from pydantic import BaseModel
from datetime import datetime


class TaskAssignmentBase(BaseModel):
    task_id: int
    user_id: str
    is_watcher: bool = False  # False => assignee; True => watcher

class TaskWatcher(BaseModel):
    user_id: str
    is_watcher: bool = True  # Always True for watchers, False for assignees

class TaskAssignmentCreate(TaskAssignmentBase):
    pass


class TaskAssignmentRead(TaskAssignmentBase):
    id: int
    assigned_at: datetime

    class Config:
        orm_mode = True
