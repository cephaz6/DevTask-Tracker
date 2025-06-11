from datetime import datetime
from sqlmodel import SQLModel
from typing import Optional, List
<<<<<<< HEAD
from .user import UserRead
=======
>>>>>>> a5bd8487c91f1e5247a15fbd694a109d3215c472


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
<<<<<<< HEAD
    user: Optional[UserRead]
=======
>>>>>>> a5bd8487c91f1e5247a15fbd694a109d3215c472

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
