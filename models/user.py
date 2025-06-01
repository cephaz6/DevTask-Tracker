import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from pydantic import EmailStr
from utils.core import generate_user_id
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from .task import Task, TaskAssignment
    from .project import ProjectMember


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)  
    user_id: str = Field(default_factory=generate_user_id, unique=True, index=True)

    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    tasks: List["Task"] = Relationship(back_populates="user")
    project_memberships: List["ProjectMember"] = Relationship(back_populates="user")
    task_assignments: List["TaskAssignment"] = Relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, user_id='{self.user_id}', email='{self.email}')>"
