from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Dict, Any
from utils.security import get_current_user
from db.database import get_session
from sqlmodel import select

from models.user import User
from models.project import Project, ProjectMember
from models.task import Task
from utils.dashboard import (
    get_admin_dashboard_data,
    get_project_dashboard_data,
    serialize_task,
    get_user_dashboard_data,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={404: {"description": "Not found"}},
)


# _____________________________ Dashboard Router _____________________________


# This router handles the dashboard endpoints for both superusers and regular users.
@router.get("/", summary="Get dashboard data for current user")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    try:
        if current_user.is_superuser:
            try:
                admin_data = get_admin_dashboard_data(session)
                return {"role": "superuser", "dashboard": admin_data}
            except Exception as e:
                # log error e
                raise HTTPException(
                    status_code=500, detail="Error fetching admin dashboard data"
                )

        try:
            # Projects owned by user
            owned_projects = (
                session.query(Project).filter(Project.owner_id == current_user.id).all()
            )
            owned_project_ids = [p.id for p in owned_projects]
        except Exception as e:
            # log error e
            raise HTTPException(status_code=500, detail="Error fetching owned projects")

        try:
            # Projects user is member of (excluding owned projects)
            member_projects = (
                session.query(ProjectMember)
                .filter(
                    ProjectMember.user_id == current_user.id,
                    ~ProjectMember.project_id.in_(owned_project_ids),
                )
                .all()
            )
        except Exception as e:
            # log error e
            raise HTTPException(
                status_code=500, detail="Error fetching project memberships"
            )

        response = {
            "role": "user",
            "owned_projects": [],
            "member_projects": [],
        }

        try:
            for project in owned_projects:
                proj_data = get_project_dashboard_data(
                    session, project, owner_view=True
                )
                response["owned_projects"].append(proj_data)
        except Exception as e:
            # log error e
            raise HTTPException(
                status_code=500, detail="Error assembling owned projects dashboard"
            )

        try:
            for pm in member_projects:
                project = session.query(Project).get(pm.project_id)
                personal_tasks = (
                    session.query(Task)
                    .filter(
                        Task.project_id == project.id,
                        Task.assignee_id == current_user.id,
                    )
                    .all()
                )
                response["member_projects"].append(
                    {
                        "project": {
                            "id": str(project.id),
                            "name": project.title,
                        },
                        "my_tasks": [serialize_task(t) for t in personal_tasks],
                    }
                )
        except Exception as e:
            # log error e
            raise HTTPException(
                status_code=500, detail="Error assembling member projects dashboard"
            )

        return response

    except Exception as e:
        # log error e (fallback)
        raise HTTPException(status_code=500, detail="Unexpected server error")


# This router is for the dashboard endpoints, which are accessible to both superusers and regular users.
@router.get("/user", summary="Get logged-in user's dashboard data")
def user_dashboard(
    session: Session = Depends(get_session), current_user=Depends(get_current_user)
):
    print(f"Current user: {current_user}")
    try:
        return get_user_dashboard_data(session=session, user=current_user)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# # This router is for the admin dashboard, which is only accessible to superusers.
@router.get("/admin", summary="Get system admin dashboard data")
def admin_dashboard(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied. Admins only.")

        return get_admin_dashboard_data(session=session)

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# # This router is for the project-specific dashboard, which is accessible to project members and owners.
@router.get("/project/{project_id}", summary="Get dashboard for a specific project")
def project_dashboard(
    project_id: str = Path(..., title="Project ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        project = session.exec(select(Project).where(Project.id == project_id)).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if user is a member or the owner
        is_owner = str(project.owner_id) == str(current_user.user_id)

        member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.user_id,
            )
        ).first()

        if not is_owner and not member:
            raise HTTPException(
                status_code=403, detail="You are not a member of this project"
            )

        return get_project_dashboard_data(
            session=session, project=project, owner_view=is_owner
        )

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
