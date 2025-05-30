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


# Get all comments for a specific task    `GET /comments/task/{task_id}`
@router.get("/{task_id}", response_model=List[TaskCommentRead])
def get_comments_for_task(task_id: int, session: Session = Depends(get_session)):
    try:
        comments = session.exec(
            select(TaskComment).where(TaskComment.task_id == task_id)
        ).all()
        return comments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Delete a comment    `DELETE /comments/{comment_id}`
@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
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

        # Authorization check
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
