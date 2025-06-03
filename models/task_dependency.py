# It’s foundational — other features like status change tracking
# and time tracking may depend on this relationship.


# It helps users define workflows and dependencies early.

from sqlmodel import SQLModel, Field, Relationship


from sqlmodel import SQLModel, Field
from typing import Optional


class TaskDependencyLink(SQLModel, table=True):
    __tablename__ = "task_dependencies"
    """Link model for task dependencies."""

    task_id: str = Field(foreign_key="tasks.id", primary_key=True)
    depends_on_id: str = Field(foreign_key="tasks.id", primary_key=True)
