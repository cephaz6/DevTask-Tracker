from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
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
    current_user: User = Depends(get_current_user),
):
    try:
        # Prevent sending notification to oneself
        if data.recipient_user_id == current_user.user_id:
            raise HTTPException(
                status_code=400, detail="Cannot send notification to yourself"
            )

        notification = Notification(**data.model_dump())
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Get all notifications for the current user    `GET /notifications` and filter by unread status
# `GET /notifications?unread=true`
@router.get("/", response_model=List[NotificationRead])
def get_notifications(
    unread: Optional[bool] = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        query = select(Notification).where(
            Notification.recipient_user_id == current_user.user_id
        )
        if unread is True:
            query = query.where(Notification.read == False)

        notifications = session.exec(
            query.order_by(Notification.created_at.desc())
        ).all()
        return notifications

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get a specific notification by ID    `GET /notifications/{notification_id}`
@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        notification = session.get(Notification, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        if notification.recipient_user_id != current_user.user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this notification"
            )

        session.delete(notification)
        session.commit()
        return {"message": "Notification deleted"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Mark a notification as read    `PUT /notifications/{notification_id}/read`
@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_as_read(
    notification_id: str = Path(
        ..., description="ID of the notification to mark as read"
    ),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        notification = session.get(Notification, notification_id)

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.recipient_user_id != current_user.user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to modify this notification"
            )

        notification.read = True
        session.add(notification)
        session.commit()
        session.refresh(notification)
        return notification

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
