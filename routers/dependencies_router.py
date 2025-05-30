from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.task_dependency import TaskDependencyLink
from db.database import get_session
from typing import List

router = APIRouter(prefix="/dependencies", tags=["Dependencies"])


@router.get("/{task_id}/dependencies", response_model=List[int])
def get_task_dependencies(task_id: int, session: Session = Depends(get_session)):
    deps = session.exec(
        select(TaskDependencyLink.depends_on_id).where(TaskDependencyLink.task_id == task_id)
    ).all()
    return deps


@router.get("/{task_id}/dependents", response_model=List[int])
def get_task_dependents(task_id: int, session: Session = Depends(get_session)):
    dependents = session.exec(
        select(TaskDependencyLink.task_id).where(TaskDependencyLink.depends_on_id == task_id)
    ).all()
    return dependents
