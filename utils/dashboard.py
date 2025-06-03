from models.user import User
from models.project import Project, ProjectMember
from models.task import Task, TaskAssignment
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlmodel import select, func
from datetime import datetime
import logging
from db.database import get_session


# _____________________________ Dashboard Utils _____________________________


def get_admin_dashboard_data(session: Session) -> dict:
    try:
        total_users = session.exec(select(func.count()).select_from(User)).one()
        total_projects = session.exec(select(func.count()).select_from(Project)).one()
        total_tasks = session.exec(select(func.count()).select_from(Task)).one()

        return {
            "total_users": total_users[0],
            "total_projects": total_projects[0],
            "total_tasks": total_tasks[0],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error fetching admin dashboard data"
        )


def get_project_dashboard_data(
    session: Session, project: Project, owner_view: bool = True
) -> dict:
    try:
        total_tasks = session.exec(
            select(func.count()).select_from(Task).where(Task.project_id == project.id)
        ).one()[0]

        completed_tasks = session.exec(
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project.id, Task.status == "completed")
        ).one()[0]

        progress_percent = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        members_count = session.exec(
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project.id)
        ).one()[0]

        return {
            "project_id": str(project.id),
            "project_name": project.title,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percent": round(progress_percent, 2),
            "members_count": members_count,
            "owner_view": owner_view,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error fetching project dashboard data"
        )


# Serialize task data for dashboard
def serialize_task(task: Task) -> dict:
    try:
        assignees = []
        watchers = []

        if task.assignments:
            for assignment in task.assignments:
                user_info = {
                    "user_id": str(assignment.user_id),
                    "assigned_at": assignment.assigned_at.isoformat(),
                }
                if assignment.is_watcher:
                    watchers.append(user_info)
                else:
                    assignees.append(user_info)

        tags = [tag.name for tag in task.tags] if task.tags else []

        dependencies = (
            [{"id": str(dep.id), "title": dep.title} for dep in task.dependencies]
            if task.dependencies
            else []
        )

        dependents = (
            [{"id": str(dep.id), "title": dep.title} for dep in task.dependents]
            if task.dependents
            else []
        )

        comments = (
            [
                {
                    "id": str(comment.id),
                    "author_id": comment.user_id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat(),
                }
                for comment in task.comments
            ]
            if task.comments
            else []
        )

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "is_completed": task.is_completed,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "estimated_time": task.estimated_time,
            "actual_time": task.actual_time,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "project_id": task.project_id,
            "owner_id": task.user_id,
            "tags": tags,
            "assignees": assignees,
            "watchers": watchers,
            "dependencies": dependencies,
            "dependents": dependents,
            "comments": comments,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error serializing task data")


# Get user dashboard data
def get_user_dashboard_data(session: Session, user: User) -> dict:
    try:
        # 1. Get projects the user owns
        owned_projects = session.exec(
            select(Project).where(Project.owner_id == user.user_id)
        ).all()

        # 2. Get projects the user is a member of (excluding owned)
        member_links = session.exec(
            select(ProjectMember).where(ProjectMember.user_id == user.user_id)
        ).all()

        member_project_ids = {
            link.project_id for link in member_links if link.project_id != user.user_id
        }

        member_projects = (
            session.exec(
                select(Project).where(
                    Project.id.in_(member_project_ids), Project.owner_id != user.user_id
                )
            ).all()
            if member_project_ids
            else []
        )

        # 3. Tasks assigned to the user
        assignments = session.exec(
            select(TaskAssignment).where(TaskAssignment.user_id == user.user_id)
        ).all()

        task_ids = [a.task_id for a in assignments]
        assigned_tasks = (
            session.exec(select(Task).where(Task.id.in_(task_ids))).all()
            if task_ids
            else []
        )

        # 4. Task summary
        completed = [task for task in assigned_tasks if task.status == "completed"]
        pending = [task for task in assigned_tasks if task.status != "completed"]

        # 5. Final structure
        return {
            "user_id": str(user.user_id),
            "full_name": f"{user.full_name}",
            "email": user.email,
            "owned_projects": [
                {"id": str(p.id), "title": p.title} for p in owned_projects
            ],
            "member_projects": [
                {"id": str(p.id), "title": p.title} for p in member_projects
            ],
            "total_assigned_tasks": len(assigned_tasks),
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "assigned_task_list": [serialize_task(task) for task in assigned_tasks],
        }

    except Exception as e:
        logging.exception("Error in get_user_dashboard_data")
        raise HTTPException(
            status_code=500, detail="Error fetching user dashboard data"
        )
