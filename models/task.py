from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
from models.tag import Tag, TaskTagLink 
from models.task_dependency import TaskDependencyLink

if TYPE_CHECKING:
    from .task_dependency import TaskDependencyLink
    from .user import User  

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None

    estimated_time: Optional[float] = 0.5  # in hours
    actual_time: Optional[float] = 0.5     # in hours

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None 

    user_id: str = Field(foreign_key="users.user_id", index=True)

    # Existing relationships
    tags: List["Tag"] = Relationship(back_populates="tasks", link_model=TaskTagLink)
    user: Optional["User"] = Relationship(back_populates="tasks")

    # New relationships for dependencies
    dependencies: List["Task"] = Relationship(
        link_model=TaskDependencyLink,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskDependencyLink.task_id",
            "secondaryjoin": "Task.id==TaskDependencyLink.depends_on_id",
            "lazy": "selectin",
            "overlaps": "dependents"
        },
        back_populates="dependents"
    )

    dependents: List["Task"] = Relationship(
        link_model=TaskDependencyLink,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskDependencyLink.depends_on_id",
            "secondaryjoin": "Task.id==TaskDependencyLink.task_id",
            "lazy": "selectin",
            "overlaps": "dependencies"
        },
        back_populates="dependencies"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', user_id='{self.user_id}')>"
