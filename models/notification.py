from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from schemas.notification import NotificationType

class Notification(SQLModel, table=True):
    """Model for user notifications."""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    recipient_user_id: str = Field(foreign_key="users.user_id")
    message: str
    related_task_id: Optional[int] = Field(default=None, foreign_key="tasks.id")
    related_project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    type: NotificationType = Field(default=NotificationType.GENERAL)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
