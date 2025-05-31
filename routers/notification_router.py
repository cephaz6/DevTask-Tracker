from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from models.notification import Notification
from schemas.notification import NotificationCreate, NotificationRead
from db.database import get_session
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Create a new notification    `POST /notifications`
@router.post("/", response_model=NotificationRead)
def create_notification(
    data: NotificationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Prevent sending notification to oneself
        if data.recipient_user_id == current_user.user_id:
            raise HTTPException(status_code=400, detail="Cannot send notification to yourself")

        notification = Notification(**data.model_dump())
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Get all notifications for the current user    `GET /notifications`
@router.get("/", response_model=list[NotificationRead])
def get_my_notifications(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        notifications = session.exec(
            select(Notification)
            .where(Notification.recipient_user_id == current_user.user_id)
            .order_by(Notification.created_at.desc())
        ).all()
        return notifications

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get a specific notification by ID    `GET /notifications/{notification_id}`
@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        notification = session.get(Notification, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        if notification.recipient_user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this notification")

        session.delete(notification)
        session.commit()
        return {"message": "Notification deleted"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
