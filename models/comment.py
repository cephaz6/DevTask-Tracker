from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class TaskComment(SQLModel, table=True):
    """Model for task comments."""

    __tablename__ = "task_comments"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)

    task_id: str = Field(foreign_key="tasks.id")
    user_id: str = Field(foreign_key="users.user_id")
    content: str
    parent_comment_id: Optional[str] = Field(
        default=None, foreign_key="task_comments.id"
    )
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships
    task: Optional["Task"] = Relationship(back_populates="comments")
    user: Optional["User"] = Relationship()

    # Threaded comments
    parent_comment: Optional["TaskComment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={"remote_side": "TaskComment.id"},
    )
    replies: List["TaskComment"] = Relationship(back_populates="parent_comment")

    def __repr__(self):
        return f"<TaskComment(id={self.id}, task_id='{self.task_id}', user_id='{self.user_id}', content='{self.content[:20]}...')>"
