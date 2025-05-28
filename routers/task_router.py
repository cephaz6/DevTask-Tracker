from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from models.user import User
from models.task import Task
from models.tag import Tag
from schemas.task import TaskCreate, TaskRead, TaskUpdate
from db.database import get_session
from utils.security import get_current_user
from typing import List
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Get all tasks    `GET /tasks`
@router.get("/", response_model=list[TaskRead])
def get_tasks(session: Session = Depends(get_session)):
    try:
        statement = select(Task)
        tasks = session.exec(statement).all()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


# Get all tasks for the current user    `GET /tasks/my-tasks`
@router.get("/my-tasks", response_model=List[TaskRead])
def get_my_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    print(f"Current user: {current_user.user_id}")  # Debugging line
    try:
        statement = select(Task).where(Task.user_id == current_user.user_id)  # <- corrected here
        tasks = session.exec(statement).all()
        return tasks
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve tasks due to a database error."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )

# Get a specific task    `GET /tasks/{task_id}`
@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Compare the task.user_id (str) with current_user.user_id (str)
        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this task")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching task")
    
    
@router.post("/", response_model=TaskRead)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Prepare task data except tags
        new_task_data = task.model_dump(exclude={"tags"})
        new_task_data["user_id"] = current_user.user_id
        new_task_data["created_at"] = datetime.now(timezone.utc)
        new_task_data["updated_at"] = datetime.now(timezone.utc)

        # Instantiate Task without tags first
        new_task = Task(**new_task_data)

        # If tags were provided, fetch Tag objects and assign
        if task.tags:
            tags = session.exec(select(Tag).where(Tag.name.in_(task.tags))).all()
            if len(tags) != len(task.tags):
                missing_tag_name = set(task.tags) - {tag.name for tag in tags}
                raise HTTPException(
                    status_code=400,
                    detail=f"Some tags not found: {missing_tag_name}"
                )
            new_task.tags = tags

        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task

    except HTTPException:
        # Reraise HTTPExceptions (like tag not found)
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")
    


# Update a task `PATCH /tasks/{task_id}`
@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    updated_task: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this task")

        update_data = updated_task.model_dump(exclude_unset=True)

        # Handle tags separately
        tag_names = update_data.pop("tags", None)
        if tag_names is not None:
            new_tags = []
            for tag_name in tag_names:
                tag = session.exec(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                new_tags.append(tag)
            task.tags = new_tags

        # Bulk update the rest
        for key, value in update_data.items():
            setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)

        return task
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")



# Delete a task    `DELETE /tasks/{task_id}`
@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        session.delete(task)
        session.commit()
        return {"message": "Task deleted successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete task")
