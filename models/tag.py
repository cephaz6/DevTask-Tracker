from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4

if TYPE_CHECKING:
    from .task import Task

# This model represents a many-to-many relationship between tasks and tags.
class TaskTagLink(SQLModel, table=True):
    task_id: Optional[str] = Field(default=None, foreign_key="tasks.id", primary_key=True)
    tag_id: Optional[str] = Field(default=None, foreign_key="tags.id", primary_key=True)
    """Link model for many-to-many relationship between tasks and tags."""


# This model allows tasks to be associated with multiple tags and vice versa.
class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[str] = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    name: str = Field(index=True, unique=True)

    tasks: List["Task"] = Relationship(
        back_populates="tags",
        link_model=TaskTagLink
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"