from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from models.task import Task
from models.user import User


class TaskCommentBase(SQLModel):
    task_id: int
    content: str

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentRead(TaskCommentBase):
    id: int
    user_id: str
    created_at: datetime
