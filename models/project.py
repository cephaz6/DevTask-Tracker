from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime


if TYPE_CHECKING:
    from .task import Task
    from .user import User  

# This model represents a project, which can have multiple members and tasks.
class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    owner_id: str = Field(foreign_key="users.user_id")
    created_at: datetime = Field(default_factory=datetime.now)

    members: List["ProjectMember"] = Relationship(back_populates="project")
    tasks: List["Task"] = Relationship(back_populates="project")


#this model represents the many-to-many relationship between projects and project members
class ProjectMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    user_id: str = Field(foreign_key="users.user_id")
    role: str = Field(default="member")  # 'owner' or 'member'

    project: "Project" = Relationship(back_populates="members")
    user: "User" = Relationship(back_populates="project_memberships")
