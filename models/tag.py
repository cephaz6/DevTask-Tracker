from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .task import Task

class TaskTagLink(SQLModel, table=True):
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tags.id", primary_key=True)

class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    tasks: List["Task"] = Relationship(
        back_populates="tags",
        link_model=TaskTagLink
    )
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"