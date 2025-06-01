from datetime import datetime
from sqlmodel import SQLModel


class TaskCommentBase(SQLModel):
    task_id: str
    content: str

class TaskCommentCreate(TaskCommentBase):
    pass

class TaskCommentRead(TaskCommentBase):
    id: str
    user_id: str
    created_at: datetime
    class Config:
        orm_mode = True

class TaskCommentSummary(SQLModel):
    id: str
    content: str
    
    class Config:
        orm_mode = True
