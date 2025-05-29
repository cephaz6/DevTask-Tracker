from datetime import datetime, timezone
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlmodel import select
from typing import List
from models.task import Task
from models.tag import Tag
from db.database import get_session
from schemas.task import TaskCreate, TaskRead, TaskUpdate
from models.user import User
from utils.security import get_current_user


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