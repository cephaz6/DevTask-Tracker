from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now}
    )
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None
