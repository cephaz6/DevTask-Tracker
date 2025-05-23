from typing import Optional, List, TYPE_CHECKING # Import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr
from datetime import datetime, timezone
from utils.core import generate_user_id


if TYPE_CHECKING:
    from .task import Task # Avoid circular import
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
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

    def __repr__(self):
        return f"<User(id={self.id}, user_id='{self.user_id}', email='{self.email}')>" 