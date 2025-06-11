from pydantic import BaseModel, EmailStr
from typing import Optional
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
