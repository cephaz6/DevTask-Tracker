from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Schema to create a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


# Schema for reading user information (response after authentication or user details)
class UserRead(BaseModel):
    user_id: str
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        # serialization settings
        orm_mode = True


class UserReadMinimal(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True # For Pydantic V2

# Schema for user login (authentication)
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Schema for updating user details (email and password)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        orm_mode = True

class UserBatchRequest(BaseModel):
    user_ids: List[str]


class DashboardStatsRead(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_assignments: int # Tasks assigned to user, not yet completed/cancelled
    active_projects: int
    recent_comments_count: int # Placeholder, or actual count if you add comment fetching logic here

# NEW: Pydantic schema for Recent Activity Item
class RecentActivityItemRead(BaseModel):
    id: str # ID of the activity (e.g., task_id, comment_id)
    type: str # e.g., "task_created", "task_completed", "comment_added", "assignment_created", "project_created"
    description: str # A human-readable description of the activity
    timestamp: datetime # When the activity occurred
    actor_name: str # Name of the user who performed the action
    related_entity_title: Optional[str] = None # Title of the related task/project
    related_entity_id: Optional[str] = None # ID of the related task/project

    class Config:
        from_attributes = True 