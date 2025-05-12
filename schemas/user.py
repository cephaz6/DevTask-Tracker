from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    password: str
