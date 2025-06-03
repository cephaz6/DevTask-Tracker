# routers/tasks/task_assignment_router.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from sqlmodel import select

from models.task import Task
from models.task import TaskAssignment
from models.project import Project
from models.user import User
from models.project import ProjectMember
from schemas.task_assignment import TaskAssignmentCreate, TaskAssignmentRead
from db.database import get_session
from utils.security import get_current_user

from utils.core import create_notification
from schemas.notification import NotificationType

router = APIRouter()


# This function checks if the current user is authorized to modify task assignments.
def _authorize_task_modification(task: Task, current_user: User, session: Session):
    """
    Returns True if current_user is allowed to modify assignments on this task:
      - Task owner (task.user_id == current_user.user_id)
      - OR Project owner (if task.project_id != None and project.owner_id == current_user.user_id)
    Otherwise, raises HTTPException(403).
    """
    # Task owner:
    if task.user_id == current_user.user_id:
        return

    # If task belongs to a project, check project owner:
    if task.project_id is not None:
        project = session.get(Project, task.project_id)
        if project and project.owner_id == current_user.user_id:
            return

    raise HTTPException(
        status_code=403, detail="Not authorized to modify task assignments"
    )


# Assign a user to a task as an assignee or watcher
@router.post("/assign", response_model=TaskAssignmentRead)
def assign_user_to_task(
    payload: TaskAssignmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        task = session.get(Task, payload.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        _authorize_task_modification(task, current_user, session)

        user = session.exec(select(User).where(User.user_id == payload.user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check for existing assignment
        assignment = session.exec(
            select(TaskAssignment).where(
                TaskAssignment.task_id == payload.task_id,
                TaskAssignment.user_id == payload.user_id,
            )
        ).first()

        if assignment:
            # CASE 1: Already assigned and is_watcher is False again → Conflict
            if not assignment.is_watcher and not payload.is_watcher:
                raise HTTPException(
                    status_code=409, detail="User is already assigned to this task."
                )

            # CASE 2: Update is_watcher if changed
            if assignment.is_watcher != payload.is_watcher:
                assignment.is_watcher = payload.is_watcher
                session.add(assignment)
                session.commit()
                session.refresh(assignment)

            return assignment

        # New assignment
        assignment = TaskAssignment(
            task_id=payload.task_id,
            user_id=payload.user_id,
            is_watcher=payload.is_watcher,
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)

        # Send notification only for new assignments (not for is_watcher updates)
        if user.user_id != current_user.user_id:
            notif_msg = (
                f"{current_user.full_name} assigned you to the task: '{task.title}'"
            )
            create_notification(
                session=session,
                recipient_user_id=user.user_id,
                message=notif_msg,
                task_id=payload.task_id,
                notif_type=NotificationType.TASK_ASSIGNMENT,
            )

        return assignment

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Add a user as a watcher to a task
@router.post("/watch", response_model=TaskAssignmentRead)
def add_watcher_to_task(
    payload: TaskAssignmentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Add a user as a 'watcher' (is_watcher=True) to a task.
    Only the task owner or project owner can do this.
    """
    try:
        # 1. Fetch task
        task = session.get(Task, payload.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # 2. Authorization check
        _authorize_task_modification(task, current_user, session)

        # 3. Validate invited user exists
        invited_user = session.exec(
            select(User).where(User.user_id == payload.user_id)
        ).first()
        if not invited_user:
            raise HTTPException(status_code=404, detail="User to watch not found")

        # 4. Prevent duplicate watcher entry
        existing = session.exec(
            select(TaskAssignment).where(
                TaskAssignment.task_id == payload.task_id,
                TaskAssignment.user_id == payload.user_id,
                TaskAssignment.is_watcher == True,
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="User is already a watcher for this task"
            )

        # 5. Create watcher entry
        assignment = TaskAssignment(
            task_id=payload.task_id, user_id=payload.user_id, is_watcher=True
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)

        if invited_user.user_id != current_user.user_id:
            notif_msg = f"{current_user.full_name} added you as a watcher to the task: '{task.title}'"
            create_notification(
                session=session,
                recipient_user_id=invited_user.user_id,
                message=notif_msg,
                notif_type=NotificationType.TASK_ASSIGNMENT,
            )
        return assignment

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# List all watchers and assignees for a task
@router.get("/{task_id}", response_model=List[TaskAssignmentRead])
def list_task_assignments(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List all watchers and assignees for a given task.
    Any project member or the task owner can view this.
    """
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # If the task is in a project, ensure current_user is a project member
        if task.project_id is not None:
            project = session.get(Project, task.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Check membership:
            membership = session.exec(
                select(ProjectMember).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == current_user.user_id,
                )
            ).first()
            if not membership:
                raise HTTPException(status_code=403, detail="Not a project member")

        # Otherwise (standalone task), only the task owner can view
        else:
            if task.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=403, detail="Not authorized to view assignments"
                )

        assignments = session.exec(
            select(TaskAssignment).where(TaskAssignment.task_id == task_id)
        ).all()
        return assignments

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Remove a watcher or an assignee from a task
@router.delete("/{assignment_id}")
def remove_task_assignment(
    assignment_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a watcher or an assignee from a task.
    Only the task owner or project owner can do this.
    """
    try:
        assignment = session.get(TaskAssignment, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Fetch task to check authorization
        task = session.get(Task, assignment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        _authorize_task_modification(task, current_user, session)

        session.delete(assignment)
        session.commit()
        return {"message": "Assignment removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
