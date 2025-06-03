import secrets, string
from typing import Optional
from sqlmodel import Session
from models.notification import Notification
from schemas.notification import NotificationType
from models.task import Task


# This file contains utility functions for the application.
# The functions are used to generate random strings for user IDs and passwords.
def generate_user_id():

    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for i in range(16))


# This function creates a notification in the database.
def create_notification(
    session: Session,
    recipient_user_id: str,
    message: str,
    notif_type: NotificationType = NotificationType.GENERAL,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
):
    try:
        # Auto-resolve project_id from task_id if not provided
        if task_id and not project_id:
            task = session.get(Task, task_id)
            if task:
                project_id = str(task.project_id) if task.project_id else None

        notification = Notification(
            recipient_user_id=recipient_user_id,
            message=message,
            type=notif_type,
            related_task_id=task_id,
            related_project_id=project_id,
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification

    except Exception as e:
        session.rollback()
        raise Exception(f"Notification failed: {str(e)}")
