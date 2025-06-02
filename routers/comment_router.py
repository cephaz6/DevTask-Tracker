import json

from datetime import datetime
from typing import Optional, List
from sqlmodel import select
from models.task import Task
from models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_session
from schemas.comment import TaskCommentCreate, TaskCommentRead
from utils.security import get_current_user
from models.comment import TaskComment
from models.project import Project
from utils.core import create_notification
from schemas.notification import NotificationType
from routers.websocket.ws_comments import active_connections

router = APIRouter(prefix="/comments", tags=["comments"])


# Add a comment to a task    `POST /comments` (supports replies with parent_comment_id)
@router.post("/", response_model=TaskCommentRead)
async def add_comment(
    comment: TaskCommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, comment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Validate parent_comment_id if provided
        if comment.parent_comment_id:
            parent_comment = session.get(TaskComment, comment.parent_comment_id)
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")
            if parent_comment.task_id != comment.task_id:
                raise HTTPException(status_code=400, detail="Parent comment task mismatch")

        new_comment = TaskComment(
            task_id=comment.task_id,
            user_id=current_user.user_id,
            content=comment.content,
            parent_comment_id=comment.parent_comment_id
        )
        session.add(new_comment)
        session.commit()
        session.refresh(new_comment)

        # Send real-time WebSocket message
        payload = {
            "type": "reply" if new_comment.parent_comment_id else "comment",
            "task_id": new_comment.task_id,
            "comment_id": new_comment.id,
            "content": new_comment.content,
            "user_id": new_comment.user_id,
            "parent_comment_id": new_comment.parent_comment_id,
            "created_at": new_comment.created_at.isoformat(),
            "full_name": current_user.full_name
        }

        for connection in active_connections.get(str(new_comment.task_id), []):
            try:
                await connection.send_text(json.dumps(payload))
            except Exception:
                # Optionally: remove dead connection
                active_connections[str(new_comment.task_id)].remove(connection)

        # Notifications
        if new_comment.parent_comment_id:
            if parent_comment.user_id != current_user.user_id:
                create_notification(
                    session=session,
                    recipient_user_id=parent_comment.user_id,
                    message=f"{current_user.full_name} replied to your comment on task '{task.title}'",
                    notif_type=NotificationType.COMMENT_REPLY,
                    task_id=comment.task_id
                )
        else:
            # Create a notification for the task owner
            if task.user_id != current_user.user_id:
                create_notification(
                    session=session,
                    recipient_user_id=task.user_id,
                    message=f"{current_user.full_name} commented on your task '{task.title}'",
                    notif_type=NotificationType.COMMENT,
                    task_id=comment.task_id
                )

        return new_comment

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))



# Get all comments for a specific task
@router.get("/{task_id}", response_model=List[TaskCommentRead])
def get_comments_for_task(task_id: str, session: Session = Depends(get_session)):
    try:
        comments = session.exec(
            select(TaskComment).where(TaskComment.task_id == task_id)
        ).all()
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete a comment
@router.delete("/{comment_id}")
def delete_comment(
    comment_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        comment = session.get(TaskComment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        task = session.get(Task, comment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        project_owner_id = None
        if task.project_id:
            project = session.get(Project, task.project_id)
            if project:
                project_owner_id = project.owner_id

        # Authorization check: Only comment author, task owner, or project owner can delete
        is_author = comment.user_id == current_user.user_id
        is_task_owner = task.user_id == current_user.user_id
        is_project_owner = project_owner_id == current_user.user_id

        if not (is_author or is_task_owner or is_project_owner):
            raise HTTPException(status_code=403, detail="You are not authorized to delete this comment")

        session.delete(comment)
        session.commit()
        return {"message": "Comment deleted successfully"}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
