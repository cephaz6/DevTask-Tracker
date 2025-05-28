from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
from models.tag import Tag, TaskTagLink
from models.task_dependency import TaskDependencyLink

if TYPE_CHECKING:
    from .user import User

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    status: str = "not_started"  # Add this if missing
    is_completed: bool = False
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None

    estimated_time: Optional[float] = 0.5
    actual_time: Optional[float] = 0.5

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    user_id: str = Field(foreign_key="users.user_id", index=True)

    tags: List["Tag"] = Relationship(back_populates="tasks", link_model=TaskTagLink)
    user: Optional["User"] = Relationship(back_populates="tasks")

    # Dependencies: Tasks this task depends on
    dependencies: List["Task"] = Relationship(
        back_populates="dependents",
        link_model=TaskDependencyLink,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskDependencyLink.task_id",
            "secondaryjoin": "Task.id==TaskDependencyLink.depends_on_id",
            "lazy": "selectin",
            "overlaps": "dependents"
        }
    )

    # Dependents: Tasks that depend on this task
    dependents: List["Task"] = Relationship(
        back_populates="dependencies",
        link_model=TaskDependencyLink,
        sa_relationship_kwargs={
            "primaryjoin": "Task.id==TaskDependencyLink.depends_on_id",
            "secondaryjoin": "Task.id==TaskDependencyLink.task_id",
            "lazy": "selectin",
            "overlaps": "dependencies"
        }
    )
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"