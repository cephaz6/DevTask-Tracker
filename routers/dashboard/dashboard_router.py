from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from utils.security import get_current_user
from db.database import get_session
from sqlmodel import select, func, or_
from datetime import datetime, timedelta

from models.user import User
from models.project import Project, ProjectMember
from models.task import Task, TaskAssignment
from models.comment import TaskComment
from schemas.user import RecentActivityItemRead, DashboardStatsRead
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
                print(f"Error fetching admin dashboard data: {e}")
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
            print(f"Error fetching owned projects: {e}")
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
            print(f"Error fetching project memberships: {e}")
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
            print(f"Error assembling owned projects dashboard: {e}")
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
            print(f"Error assembling member projects dashboard: {e}")
            raise HTTPException(
                status_code=500, detail="Error assembling member projects dashboard"
            )

        return response

    except Exception as e:
        # log error e (fallback)
        print(f"Unexpected error in get_dashboard: {e}")
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


@router.get("/stats", response_model=DashboardStatsRead)
def get_dashboard_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves aggregated statistics for the current user's dashboard.
    """
    try:
        # --- Total Tasks (created by current user OR assigned to current user) ---
        # Get tasks created by the user (Task.user_id is the creator/owner)
        tasks_created_by_user_query = select(Task.id).where(Task.user_id == current_user.user_id)
        tasks_created_by_user_ids = session.exec(tasks_created_by_user_query).all()
        
        # Get tasks where the user is an assignee
        tasks_assigned_to_user_query = select(TaskAssignment.task_id).where(TaskAssignment.user_id == current_user.user_id)
        tasks_assigned_to_user_ids = session.exec(tasks_assigned_to_user_query).all()

        # Combine unique task IDs from both created and assigned tasks
        all_relevant_task_ids = list(set(tasks_created_by_user_ids + tasks_assigned_to_user_ids))
        total_tasks_count = len(all_relevant_task_ids)

        # Fetch actual Task objects for pending/completed status checks from the relevant tasks
        all_relevant_tasks = []
        if all_relevant_task_ids:
            all_relevant_tasks = session.exec(
                select(Task).where(Task.id.in_(all_relevant_task_ids))
            ).all()

        # --- Completed Tasks ---
        completed_tasks_count = sum(1 for task in all_relevant_tasks if task.status == "completed")

        # --- Pending Assignments (tasks assigned to current user, not completed/cancelled) ---
        pending_assignments_count = sum(
            1 for task in all_relevant_tasks if task.id in tasks_assigned_to_user_ids and task.status not in ["completed", "cancelled"]
        )
        
        # --- Active Projects (projects where the current user is a member or owner) ---
        # Find project IDs where the user is an owner or member
        active_project_ids_query = select(ProjectMember.project_id).where(ProjectMember.user_id == current_user.user_id).distinct()
        active_projects_count = session.exec(active_project_ids_query).scalar_one_or_none() or 0

        # --- Recent Comments Count ---
        # Count comments on tasks the user is involved in (owner or assignee)
        recent_comments_count_query = select(func.count(TaskComment.id)).where(
            TaskComment.task_id.in_(all_relevant_task_ids),
            TaskComment.created_at >= datetime.utcnow() - timedelta(days=7) # Comments in last 7 days
        )
        recent_comments_count = session.exec(recent_comments_count_query).scalar_one_or_none() or 0


        return DashboardStatsRead(
            total_tasks=total_tasks_count,
            completed_tasks=completed_tasks_count,
            pending_assignments=pending_assignments_count,
            active_projects=active_projects_count,
            recent_comments_count=recent_comments_count,
        )

    except Exception as e:
        # Log the detailed error for debugging purposes
        print(f"Error fetching dashboard stats for user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics."
        )


@router.get("/recent-activities", response_model=List[RecentActivityItemRead])
def get_recent_activities(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
):
    """
    Retrieves recent activities related to the current user's tasks and projects.
    Activities include new tasks, task status changes (e.g., completed), comments, and assignments.
    """
    activities = []
    
    # Define a time threshold for "recent" (e.g., last 30 days)
    time_threshold = datetime.utcnow() - timedelta(days=30)

    # 1. Get relevant tasks (created by user or assigned to user)
    # This helps filter activities to only what the current user is involved with
    relevant_task_ids_query = select(Task.id).where(
        or_(
            Task.user_id == current_user.user_id,
            Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == current_user.user_id))
        )
    ).distinct()
    relevant_task_ids = session.exec(relevant_task_ids_query).all()


    # 2. Fetch Recent Tasks (created or status changed)
    # Tasks created by user
    recent_created_tasks = session.exec(
        select(Task, User)
        .join(User, Task.user_id == User.user_id) # Join to get creator's name
        .where(
            Task.user_id == current_user.user_id,
            Task.created_at >= time_threshold
        )
        .order_by(Task.created_at.desc())
        .limit(limit)
    ).all()
    for task, creator_user in recent_created_tasks:
        activities.append(RecentActivityItemRead(
            id=task.id,
            type="task_created",
            description=f"Task '{task.title}' was created.",
            timestamp=task.created_at,
            actor_name=creator_user.full_name or creator_user.email.split('@')[0],
            related_entity_title=task.title,
            related_entity_id=task.id
        ))

    # Tasks completed by user (or where user is owner and task is completed)
    recent_completed_tasks = session.exec(
        select(Task, User)
        .join(User, Task.user_id == User.user_id) # Join to get owner's name
        .where(
            Task.status == "completed",
            Task.updated_at >= time_threshold, # Check updated_at for status changes
            or_(
                Task.user_id == current_user.user_id, # User owns the task
                Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == current_user.user_id)) # User is assigned to task
            )
        )
        .order_by(Task.updated_at.desc())
        .limit(limit)
    ).all()
    for task, actor_user in recent_completed_tasks:
        activities.append(RecentActivityItemRead(
            id=task.id,
            type="task_completed",
            description=f"Task '{task.title}' was completed.",
            timestamp=task.updated_at,
            actor_name=actor_user.full_name or actor_user.email.split('@')[0],
            related_entity_title=task.title,
            related_entity_id=task.id
        ))


    # 3. Fetch Recent Comments (on relevant tasks)
    recent_comments = session.exec(
        select(TaskComment, User, Task)
        .join(User, TaskComment.user_id == User.user_id) # Commenter
        .join(Task, TaskComment.task_id == Task.id)     # Related task
        .where(
            TaskComment.task_id.in_(relevant_task_ids), # Only comments on user's relevant tasks
            TaskComment.created_at >= time_threshold
        )
        .order_by(TaskComment.created_at.desc())
        .limit(limit)
    ).all()
    for comment, actor_user, task_obj in recent_comments:
        activities.append(RecentActivityItemRead(
            id=comment.id,
            type="comment_added",
            description=f"'{comment.content[:50]}...' added to task '{task_obj.title}'.", # Truncate comment
            timestamp=comment.created_at,
            actor_name=actor_user.full_name or actor_user.email.split('@')[0],
            related_entity_title=task_obj.title,
            related_entity_id=task_obj.id
        ))

    # 4. Fetch Recent Assignments (where current user is the assignee)
    recent_assignments = session.exec(
        select(TaskAssignment, User, Task)
        .join(User, TaskAssignment.user_id == User.user_id) # The assignee
        .join(Task, TaskAssignment.task_id == Task.id)     # The task assigned
        .where(
            TaskAssignment.user_id == current_user.user_id,
            TaskAssignment.created_at >= time_threshold # Assuming TaskAssignment has a created_at
        )
        .order_by(TaskAssignment.created_at.desc())
        .limit(limit)
    ).all()
    for assignment, assignee_user, task_obj in recent_assignments:
        activities.append(RecentActivityItemRead(
            id=assignment.id,
            type="assignment_created",
            description=f"You were assigned to task '{task_obj.title}'.",
            timestamp=assignment.created_at,
            actor_name=assignee_user.full_name or assignee_user.email.split('@')[0], # This will be current_user
            related_entity_title=task_obj.title,
            related_entity_id=task_obj.id
        ))


    # Sort all activities by timestamp in descending order and limit
    sorted_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)[:limit]

    return sorted_activities