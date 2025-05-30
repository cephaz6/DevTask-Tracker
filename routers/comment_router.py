from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from models.task import Task
from models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_session
from schemas.comment import TaskCommentCreate, TaskCommentRead
from utils.security import get_current_user
from models.comment import TaskComment

router = APIRouter(prefix="/comments", tags=["comments"])

# Add a comment to a task    `POST /comments`
@router.post("/", response_model=TaskCommentRead)
def add_comment(
    comment: TaskCommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, comment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        new_comment = TaskComment(
            task_id=comment.task_id,
            user_id=current_user.user_id,
            content=comment.content
        )
        session.add(new_comment)
        session.commit()
        session.refresh(new_comment)
        return new_comment

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
