from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models.project import Project, ProjectMember
from models.user import User
from schemas.project import ProjectCreate, ProjectRead, ProjectMemberRead

from db.database import get_session
from utils.security import get_current_user


router = APIRouter()

# Create a new project    `POST /projects`
@router.post("/", response_model=ProjectRead)
def create_project(
    project: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        new_project = Project(**project.model_dump(), owner_id=current_user.user_id)
        session.add(new_project)
        session.commit()
        session.refresh(new_project)

        membership = ProjectMember(
            project_id=new_project.id,
            user_id=current_user.user_id,
            role="owner"
        )
        session.add(membership)
        session.commit()

        return new_project
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# List all projects for the current user    `GET /projects`
@router.get("/", response_model=List[ProjectRead])
def list_projects(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        projects = (
            session.query(Project)
            .join(ProjectMember)
            .filter(ProjectMember.user_id == current_user.user_id)
            .all()
        )
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get a specific project by ID    `GET /projects/{project_id}`
@router.get("/{project_id}", response_model=ProjectRead)
def get_project_by_id(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        is_member = session.query(ProjectMember).filter_by(
            project_id=project_id, user_id=current_user.user_id
        ).first()

        if not is_member:
            raise HTTPException(status_code=403, detail="Not a project member")

        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update a project    `PUT /projects/{project_id}`
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Only the owner can delete the project")

        session.delete(project)
        session.commit()
        return {"message": "Project deleted successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
