from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id: int
    owner_id: str
    created_at: datetime

    class Config:
        orm_mode = True

class ProjectMemberRead(BaseModel):
    id: int
    user_id: str
    project_id: int
    role: str

    class Config:
        orm_mode = True


class ProjectMemberCreate(BaseModel):
    project_id: int
    user_id: str

class ProjectRoleUpdate(BaseModel):
    project_id: int
    user_id: str
    role: str

