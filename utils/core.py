import secrets, string
from sqlmodel import Session
from models.notification import Notification
from schemas.notification import NotificationType



# This file contains utility functions for the application.
# The functions are used to generate random strings for user IDs and passwords.
def generate_user_id():

    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))


# Notification Method
def create_notification(
    session: Session,
    recipient_user_id: str,
    message: str,
    notif_type: NotificationType = NotificationType.GENERAL
):
    try:
        notification = Notification(
            recipient_user_id=recipient_user_id,
            message=message,
            type=notif_type
        )
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification
    except Exception as e:
        session.rollback()
        raise Exception(f"Notification failed: {str(e)}")
    


