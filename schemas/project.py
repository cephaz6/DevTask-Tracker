from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from .task import TaskRead


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

class ProjectMemberRemoveRequest(BaseModel):
    project_id: str
    user_id: str

class ProjectMemberCreate(BaseModel):
    project_id: str
    user_identifier: str  # Single field to receive either user_id or email
    role: str = "member"  

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

class ProjectMemberReadWithUser(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: str
    # FIX: Explicitly set default to None for Optional field if it's not being loaded consistently
    user: Optional[UserReadMinimal] = None 

    class Config:
        orm_mode = True

    class Config:
        orm_mode = True

class TaskReadMinimal(BaseModel):
    id: str
    title: str
    status: str # Only include fields you want to expose
    priority: str

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
    tasks: List[TaskRead] = [] # List of associated tasks

    class Config:
        orm_mode = True