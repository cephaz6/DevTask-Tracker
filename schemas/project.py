from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str
    owner_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class ProjectMemberRead(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: str

    class Config:
        orm_mode = True


class ProjectMemberCreate(BaseModel):
    project_id: str
    user_id: str


class ProjectRoleUpdate(BaseModel):
    project_id: str
    user_id: str
    role: str
