from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass



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


class ProjectMemberReadWithUser(ProjectMemberRead):
    full_name: str | None
    email: str | None
    # Add other user fields if needed

class UserReadMinimal(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None

class ProjectMemberReadWithUser(BaseModel): # This is the ProjectMemberRead for frontend consumption
    id: str
    user_id: str
    project_id: str
    role: str
    user: Optional[UserReadMinimal] # Nested user data

    class Config:
        orm_mode = True

class TaskReadMinimal(BaseModel):
    id: str
    title: str
    status: str # Only include fields you want to expose

    class Config:
        orm_mode = True

class ProjectRead(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    owner_id: str
    created_at: datetime
    # owner: Optional[UserReadMinimal] # If you want to expose owner details directly

    members: List[ProjectMemberReadWithUser] = [] # List of project members with user details
    tasks: List[TaskReadMinimal] = [] # List of associated tasks

    class Config:
        orm_mode = True