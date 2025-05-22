from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.user import User
from models.task import Task
from schemas.task import TaskCreate, TaskRead
from db.database import get_session
from utils.security import get_current_user
from typing import List
from datetime import datetime

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

# Get all tasks for the current user    `GET /tasks/my-tasks`
@router.get("/tasks/my-tasks")
def get_my_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    statement = select(Task).where(Task.user_id == current_user.user_id)
    tasks = session.exec(statement).all()
    return tasks
    

# Create a new task    `POST /tasks`
@router.post("/", response_model=TaskRead)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        new_task = Task(**task.model_dump(), user_id=current_user.user_id)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task
    except Exception as e:
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
