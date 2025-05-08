from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.database import get_session
from models.task import Task
from schemas.task import TaskCreate, TaskRead

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


# Create a new task    `POST /tasks`
@router.post("/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    try:
        new_task = Task.model_validate(task)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return new_task
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to create task")