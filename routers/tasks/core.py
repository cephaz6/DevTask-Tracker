from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models.task import Task  
from schemas.task import TaskRead  
from db.database import get_session 

router = APIRouter()

@router.get("/filter", response_model=List[TaskRead])
def filter_tasks_by_status(status: str, session: Session = Depends(get_session)):
    """
    Filter tasks by their status (e.g., 'not_started', 'in_progress', 'completed')
    """
    tasks = session.query(Task).filter(Task.status == status).all()
    return tasks


@router.get("/dependent-on/{task_id}", response_model=List[TaskRead])
def get_tasks_that_depend_on(task_id: int, session: Session = Depends(get_session)):
    """
    Return all tasks that depend on a given task (i.e., where the given task is a dependency)
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.dependents
