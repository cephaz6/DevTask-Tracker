from typing import List, Optional
from pydantic import BaseModel

class TaskDependencyBase(BaseModel):
    dependencies: Optional[List[int]] = []

class TaskCreate(TaskDependencyBase):
    title: str
    description: Optional[str] = None
    # Include other fields as needed

class TaskUpdate(TaskDependencyBase):
    title: Optional[str] = None
    description: Optional[str] = None
    # Include other optional update fields

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    dependencies: List["TaskReadNested"] = []
    dependents: List["TaskReadNested"] = []

    class Config:
        orm_mode = True

class TaskReadNested(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True

TaskRead.model_rebuild()
