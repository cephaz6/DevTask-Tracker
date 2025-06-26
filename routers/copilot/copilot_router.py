# routers/copilot.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from models.project import Project, ProjectMember 
from models.task import Task, TaskAssignment
from schemas.copilot import AIGeneratedProject, PromptRequest, GeneratedProject
from utils.security import get_session, get_current_user
from utils.llm import call_gpt_from_user_prompt

router = APIRouter(prefix="/copilot", tags=["CoPilot"])

@router.post("/save-generated-project")
def save_generated_project(
    data: AIGeneratedProject,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # 1. Create project
    project = Project(
        id=uuid4().hex,
        title=data.title,
        description=data.description,
        owner_id=current_user.user_id,
    )
    session.add(project)
    session.commit()

    # 2. Add owner as a ProjectMember
    project_member = ProjectMember(
        project_id=project.id,
        user_id=current_user.user_id,
        role="owner"
    )
    session.add(project_member)

    # 3. Create tasks and assign to owner
    for task_data in data.tasks:
        task = Task(
            id=uuid4().hex,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            estimated_time=task_data.estimated_time,
            due_date=task_data.due_date,
            project_id=project.id,
            user_id=current_user.user_id,
        )
        session.add(task)
        session.flush()

        # Optional: Assign task to the owner as well
        assignment = TaskAssignment(
            task_id=task.id,
            user_id=current_user.user_id,
            is_watcher=False
        )
        session.add(assignment)

    session.commit()
    return {"message": "Project and tasks saved successfully", "project_id": project.id}



@router.post("/generate-tasks", response_model=GeneratedProject)
def generate_tasks_from_prompt(
    data: PromptRequest
):
    return call_gpt_from_user_prompt(data.prompt)