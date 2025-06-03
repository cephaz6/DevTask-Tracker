from datetime import datetime
from sqlmodel import SQLModel
from typing import Optional, List


class TaskCommentBase(SQLModel):
    task_id: str
    content: str
    parent_comment_id: Optional[str] = None  # Parent comment for threaded comments


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


class TaskCommentWithReplies(TaskCommentRead):
    replies: List["TaskCommentWithReplies"] = []


TaskCommentWithReplies.model_rebuild()
