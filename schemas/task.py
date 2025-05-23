from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    is_completed: bool = False

    class Config:
        orm_mode = True 

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
        model_config = {"from_attributes": True}