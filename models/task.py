# models/task.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List # Import TYPE_CHECKING
from datetime import datetime, timezone
from models.tag import Tag, TaskTagLink # Assuming tag.py is in the same directory


if TYPE_CHECKING:
    from .user import User # Assuming user.py is in the same directory

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None 

    user_id: str = Field(foreign_key="users.user_id", index=True) 
    tags: List[Tag] = Relationship(back_populates="tasks", link_model=TaskTagLink)

    user: Optional["User"] = Relationship(back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"