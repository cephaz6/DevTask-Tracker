from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from models.user import User
from models.task import Task
from schemas.task import TaskCreate, TaskRead
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


# Get a task by ID    `GET /tasks/{task_id}`
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
        if task.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this task")
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching task")
    
    
@router.post("/", response_model=TaskRead) 
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Check if the user is authenticated
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        

        new_task_data = task.model_dump()
        new_task_data["user_id"] = current_user.user_id
        new_task_data["created_at"] = datetime.now(timezone.utc)
        new_task_data["updated_at"] = datetime.now(timezone.utc) 

        new_task = Task(**new_task_data)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task
    except Exception as e:
        session.rollback() # Ensure rollback on error
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")
   

# Update a task    `PUT /tasks/{task_id}`
@router.put("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, updated_task: TaskCreate, session: Session = Depends(get_session)):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.title = updated_task.title
        task.description = updated_task.description
        task.status = updated_task.status

        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update task")


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
