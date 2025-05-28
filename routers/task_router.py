from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from models.user import User
from models.task import Task
from models.task_dependency import TaskDependencyLink
from models.tag import Tag
from schemas.task import TaskCreate, TaskRead, TaskUpdate
from db.database import get_session
from utils.security import get_current_user
from typing import List
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/tasks", tags=["Tasks"])




# _________________________functions definition____________

MAX_TAGS = 3

# Function to validate and append tags to a task
def validate_and_append_tags(task: Task, tag_names: List[str], session: Session):
    existing_tag_names = {tag.name for tag in task.tags}

    for tag_name in tag_names:
        tag_name = tag_name.strip()

        if not tag_name or tag_name in existing_tag_names:
            continue  # skip empty or duplicate tags

        if len(existing_tag_names) >= MAX_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"Each task can have a maximum of {MAX_TAGS} unique tags."
            )

        tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
        if not tag:
            tag = Tag(name=tag_name)
            session.add(tag)
            session.flush()

        task.tags.append(tag)
        existing_tag_names.add(tag_name)

# ________________________end of functions definition___________________________



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
    

# Create a new task    `POST /tasks`    
@router.post("/", response_model=TaskRead)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Prepare task data except tags and dependencies
        new_task_data = task.model_dump(exclude={"tags", "dependency_ids"})
        new_task_data["user_id"] = current_user.user_id
        new_task_data["created_at"] = datetime.now(timezone.utc)
        new_task_data["updated_at"] = datetime.now(timezone.utc)

        new_task = Task(**new_task_data)

        # Handle tags
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
        session.flush()  # To get new_task.id before setting dependencies

        # Handle dependencies
        if task.dependency_ids:
            dependencies = session.exec(
                select(Task).where(Task.id.in_(task.dependency_ids))
            ).all()
            if len(dependencies) != len(task.dependency_ids):
                missing = set(task.dependency_ids) - {t.id for t in dependencies}
                raise HTTPException(400, detail=f"Some dependencies not found: {missing}")
            new_task.dependencies = dependencies

        session.commit()
        session.refresh(new_task)
        return new_task

    except HTTPException:
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

        # Tag processing (clean + validated)
        tag_names = update_data.pop("tags", None)
        if tag_names is not None:
            validate_and_append_tags(task, tag_names, session)

        # Update other fields
        for key, value in update_data.items():
            setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)

        return task

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")



#remove tags from a task    `DELETE /tasks/{task_id}/remove-tags`
@router.delete("/{task_id}/tags/{tag_name}", response_model=TaskRead)
def remove_tag_from_task(
    task_id: int,
    tag_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    tag_name = tag_name.strip()
    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    original_tags = task.tags[:]
    task.tags = [tag for tag in original_tags if tag.name != tag_name]

    if len(task.tags) == len(original_tags):
        raise HTTPException(status_code=404, detail=f"Tag '{tag_name}' not found in task")

    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()
    session.refresh(task)

    return task


# Delete a task    `DELETE /tasks/{task_id}`
@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this task")

        session.delete(task)
        session.commit()
        return {"message": "Task deleted successfully"}
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete task")
    


# update task dependencies    `PUT /tasks/{task_id}/dependencies`
@router.put("/{task_id}/dependencies", response_model=TaskRead)
def set_task_dependencies(
    task_id: int,
    dependency_ids: List[int],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if task_id in dependency_ids:
            raise HTTPException(status_code=400, detail="Task cannot depend on itself")

        dependencies = session.exec(
            select(Task).where(Task.id.in_(dependency_ids))
        ).all()

        if len(dependencies) != len(dependency_ids):
            raise HTTPException(status_code=400, detail="Invalid dependency ID(s)")
        if any(dep.user_id != current_user.user_id for dep in dependencies):
            raise HTTPException(status_code=403, detail="Cross-user linking not allowed")

        # Clear old links
        session.exec(TaskDependencyLink).filter(TaskDependencyLink.task_id == task_id).delete()

        # Add new links
        links = [
            TaskDependencyLink(task_id=task_id, depends_on_id=dep_id)
            for dep_id in dependency_ids
        ]
        session.add_all(links)

        task.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(task)

        return task

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Dependency update failed: {str(e)}")
