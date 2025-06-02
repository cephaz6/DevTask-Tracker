from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    GENERAL = "general"
    COMMENT = "comment"
    COMMENT_REPLY = "comment_reply"
    TASK_ASSIGNMENT = "task_assignment"
    PROJECT_INVITE = "project_invite"

class NotificationBase(BaseModel):
    recipient_user_id: str
    message: str
    related_project_id: Optional[str] = None

class NotificationCreate(BaseModel):
    recipient_user_id: str
    message: str
    related_task_id: Optional[str] = None
    related_project_id: Optional[str] = None
    type: NotificationType = NotificationType.GENERAL

class NotificationRead(NotificationCreate):
    id: str
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
