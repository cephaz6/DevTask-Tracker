from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from models.task import Task
from schemas.task import TaskRead
from db.database import get_session

router = APIRouter()


# Task Filtering by status    `GET /tasks/filter`
@router.get("/filter", response_model=List[TaskRead])
def filter_tasks_by_status(status: str, session: Session = Depends(get_session)):
    tasks = session.query(Task).filter(Task.status == status).all()
    return tasks


# Get all tasks    `GET /tasks` dependent on other tasks
@router.get("/dependent-on/{task_id}", response_model=List[TaskRead])
def get_tasks_that_depend_on(task_id: str, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.dependents


# Get all tasks with estimated and actual time
@router.get("/time-tracking/report")
def get_time_tracking_report(session: Session = Depends(get_session)):
    """
    Fetch all tasks with both estimated_time and actual_time
    Returns a summary showing time difference for each
    """
    tasks = (
        session.query(Task)
        .filter(Task.estimated_time.isnot(None), Task.actual_time.isnot(None))
        .all()
    )

    report = []
    for task in tasks:
        time_diff = task.actual_time - task.estimated_time
        report.append(
            {
                "task_id": task.id,
                "title": task.title,
                "estimated_time": task.estimated_time,
                "actual_time": task.actual_time,
                "time_difference": time_diff,
                "status": task.status,
            }
        )

    return report
