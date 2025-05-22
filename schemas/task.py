from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    is_completed: bool = False
    user_id: str
    # user_id: str = Field(foreign_key="users.user_id")  # Foreign key to User table
    # user: Optional[User] = Relationship(back_populates="tasks")  # Relationship to User model
    



class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_completed: bool
    priority: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    user_id: str

    class Config:
        orm_mode = True
