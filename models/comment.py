from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .task import Task
    from .user import User 


class TaskComment(SQLModel, table=True):
    """Model for task comments."""
    __tablename__ = "taskcomments"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id")
    user_id: str = Field(foreign_key="users.user_id")
    content: str
    created_at: datetime = Field(default_factory=datetime.now)

    # Relationships (optional for joins)
    task: Optional["Task"] = Relationship(back_populates="comments")
    user: Optional["User"] = Relationship()
    
