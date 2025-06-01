from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_session
from utils.security import get_current_user
from sqlalchemy import select

from models.project import ProjectMember, Project
from models.user import User
from schemas.project import ProjectMemberCreate, ProjectMemberRead, ProjectRoleUpdate

router = APIRouter()


# Invite a user to a project    `POST /project-members/invite`
@router.post("/invite", response_model=ProjectMemberRead)
def invite_user_to_project(
    invite: ProjectMemberCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Check that project exists
        project = session.get(Project, invite.project_id)
        if not project:
            raise HTTPException(status_code=403, detail="Project not found")

        # Only owner can invite
        if project.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Only the project owner can invite users")

        # Prevent self-invitation
        if invite.user_id == current_user.user_id:
            raise HTTPException(status_code=400, detail="Owner cannot invite themselves")

        # Ensure invited user exists
        invited_user = session.exec(
            select(User).where(User.user_id == invite.user_id)
        ).first()
        if not invited_user:
            raise HTTPException(status_code=404, detail="Invited user not found")

        # Prevent duplicate invitations
        existing_member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == invite.project_id,
                ProjectMember.user_id == invite.user_id
            )
        ).first()
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member of this project")

        # All good, create membership
        member = ProjectMember(
            user_id=invite.user_id,
            project_id=invite.project_id,
            role="member"
        )
        session.add(member)
        session.commit()
        session.refresh(member)
        return member

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# List all members of a project    `GET /project-members/{project_id}/members`
@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
def list_project_members(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        members = session.query(ProjectMember).filter_by(project_id=project_id).all()
        return members
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update a member's role in a project    `PATCH /project-members/role`
@router.patch("/role")
def update_member_role(
    payload: ProjectRoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        project = session.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Only the owner can update roles")

        member = session.query(ProjectMember).filter_by(
            project_id=payload.project_id,
            user_id=payload.user_id
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="User not a project member")

        member.role = payload.role
        session.commit()
        return {"message": "Member role updated"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Remove a member from a project    `DELETE /project-members/remove`
@router.delete("/remove")
def remove_project_member(
    payload: ProjectMemberCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        project = session.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Only the owner can remove members")

        member = session.query(ProjectMember).filter_by(
            project_id=payload.project_id,
            user_id=payload.user_id
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="User not a project member")

        session.delete(member)
        session.commit()
        return {"message": "Member removed successfully"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
