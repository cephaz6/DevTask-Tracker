from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session


from db.database import get_session
from models.task import Task
from schemas.task import TaskCreate, TaskRead

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    new_task = Task.model_validate(task)
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task
