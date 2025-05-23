from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from schemas.tag import TagReadNested

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    is_completed: bool = False
    tags: Optional[List[int]] = []

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
    tags: List[TagReadNested] = []

    class Config:
        model_config = {"from_attributes": True}
        orm_mode = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
