from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload 
from db.database import get_session
from utils.security import get_current_user
from utils.core import create_notification
from sqlalchemy import select  
from typing import Optional

from models.project import ProjectMember, Project
from models.user import User
from schemas.notification import NotificationType
from models.notification import Notification
from schemas.project import ProjectMemberCreate,ProjectMemberRemoveRequest, ProjectMemberReadWithUser, ProjectInvite, ProjectMemberRead, ProjectRoleUpdate

router = APIRouter()


# Invite a user to a project    `POST /project-members/invite`
@router.post("/invite", status_code=status.HTTP_201_CREATED)
def invite_user_to_project(
    invite: ProjectMemberCreate,  # Expects ProjectMemberCreate with 'user_identifier'
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1. Check that project exists
        project = session.get(Project, invite.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # 2. Only owner can invite
        if project.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can invite users."
            )

        # 3. Find the invited user by user_identifier (email or user_id)
        invited_user: Optional[User] = None
        identifier = invite.user_identifier.strip()

        if "@" in identifier:
            invited_user = session.exec(select(User).where(User.email == identifier)).scalar_one_or_none()
        else:
            invited_user = session.exec(select(User).where(User.user_id == identifier)).scalar_one_or_none()

        if not invited_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if invited_user.user_id == current_user.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot invite yourself.")

        # 4. Check if already a member
        existing_member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == invite.project_id,
                ProjectMember.user_id == invited_user.user_id
            )
        ).scalar_one_or_none()

        if existing_member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a project member.")

        # 5. Check for existing unread invite notification
        existing_invite = session.exec(
            select(Notification).where(
                Notification.recipient_user_id == invited_user.user_id,
                Notification.related_project_id == invite.project_id,
                Notification.type == NotificationType.PROJECT_INVITE,
                Notification.is_read == False,
            )
        ).first()

        if existing_invite:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has already been invited to this project.")

        # 6. Send a notification invite
        message = f"You've been invited to join the project '{project.title}' by {current_user.full_name or current_user.email}."
        

        create_notification(
            session=session,
            recipient_user_id=invited_user.user_id,
            message=message,
            notif_type=NotificationType.PROJECT_INVITE,
            project_id=invite.project_id
        )

        return {"detail": f"Invitation sent to {invited_user.email or invited_user.user_id}"}

    except HTTPException as http_e:
        session.rollback()
        raise http_e
    except Exception as e:
        session.rollback()
        print(f"Error during project invitation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected server error occurred.")



# List all members of a project    `GET /project-members/{project_id}/members`
# Then in your endpoint:
@router.get("/{project_id}/members", response_model=list[ProjectMemberReadWithUser])
def list_project_members(
    project_id: str,
    session: Session = Depends(get_session), # Assuming get_session is your DB session dependency
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a list of members for a specific project.
    Eager-loads user details for each project member.
    """
    try:
        # --- Access Control Check ---
        # Ensure the current user is a member of the project they are trying to query members for.
        project_access_check = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == current_user.user_id
            )
        ).first()

        if not project_access_check:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view members of this project. You must be a member."
            )
        # --- End Access Control Check ---

        # Load ProjectMember objects and eagerly load their associated User details.
        # Using selectinload for efficient loading of relationships in a list.
        members = session.exec(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user)) # Only selectinload here
            .where(ProjectMember.project_id == project_id)
        ).scalars().all()

        # Explicitly validate and convert each ORM object to the Pydantic response model.
        # This provides a more explicit input type for Pydantic's validation.
        return [ProjectMemberReadWithUser.model_validate(member.model_dump()) for member in members]

    except HTTPException as e:
        # Re-raise FastAPI HTTPExceptions directly
        raise e
    except Exception as e:
        # Catch any other unexpected errors, log them, and return a generic 500 error
        print(f"Error in list_project_members for project {project_id} by user {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while fetching project members."
        )



# Update a member's role in a project    `PATCH /project-members/role`
@router.patch("/role")
def update_member_role(
    payload: ProjectRoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        project = session.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=403, detail="Only the owner can update roles"
            )

        member = (
            session.query(ProjectMember)
            .filter_by(project_id=payload.project_id, user_id=payload.user_id)
            .first()
        )

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
    payload: ProjectMemberRemoveRequest, # Use the new, specific schema for removal
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1. Check that project exists
        project = session.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # 2. Only project owner can remove members
        if project.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can remove members."
            )
        
        # 3. Prevent owner from removing themselves if they are the ONLY owner
        # This is a critical edge case to prevent projects from becoming ownerless.
        # If the project can have multiple owners, you might allow owners to remove each other
        # as long as at least one owner remains. For simplicity, this assumes a single owner.
        if payload.user_id == project.owner_id and current_user.user_id == project.owner_id:
            # Check if there's at least one other owner before allowing owner to remove themselves
            # This logic depends on your 'role' management. Assuming 'owner' is a distinct role.
            all_members_in_project = session.exec(
                select(ProjectMember).where(ProjectMember.project_id == project.id)
            ).all()

            other_owners_exist = False
            for member in all_members_in_project:
                if member.role == "owner" and member.user_id != payload.user_id:
                    other_owners_exist = True
                    break
            
            if not other_owners_exist and payload.user_id == project.owner_id:
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the sole project owner without assigning another owner first."
                )


        # 4. Find the specific project member to remove using new query syntax
        member_to_remove = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == payload.project_id,
                ProjectMember.user_id == payload.user_id,
            )
        ).scalar_one_or_none() # Use scalar_one_or_none for single result

        if not member_to_remove:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not a member of this project or member not found.")
        
        # 5. Perform the deletion
        session.delete(member_to_remove)
        session.commit()
        
        # 6. Return a success message (FastAPI will serialize it to JSON)
        return {"message": "Member removed successfully."}

    except HTTPException as http_e:
        session.rollback()
        raise http_e # Re-raise FastAPI's HTTPExceptions directly
    except Exception as e:
        session.rollback()
        # Log the unexpected error for debugging on the server side
        print(f"An unexpected error occurred during project member removal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected server error occurred: {str(e)}")
    

# Accetpt a Project Membership Invitation
@router.post("/accept-invite", response_model=ProjectMemberRead)
def accept_project_invite(
    invite_data: ProjectInvite,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user_id in the request matches the authenticated user
    if invite_data.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this invite.")

    # 1. Check if the notification exists for this user and project
    notif = session.exec(
        select(Notification).where(
            Notification.recipient_user_id == current_user.user_id,
            Notification.related_project_id == invite_data.project_id,
            Notification.type == NotificationType.PROJECT_INVITE,
            Notification.is_read == False
        )
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="No pending project invite found.")

    # 2. Check if already a member
    existing = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == invite_data.project_id,
            ProjectMember.user_id == current_user.user_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a project member.")

    # 3. Add to project
    member = ProjectMember(
        project_id=invite_data.project_id,
        user_id=current_user.user_id,
        role="member"  # default role
    )
    session.add(member)

    # 4. Mark notification as read
    notif.is_read = True

    session.commit()
    session.refresh(member)
    return member

# Decline Project memebership invitation
@router.post("/decline-invite")
def decline_project_invite(
    invite_data: ProjectInvite,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user_id in the request matches the authenticated user
    if invite_data.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to decline this invite.")

    # 1. Locate the notification
    notif = session.exec(
        select(Notification).where(
            Notification.recipient_user_id == current_user.user_id,
            Notification.related_project_id == invite_data.project_id,
            Notification.type == NotificationType.PROJECT_INVITE,
            Notification.is_read == False
        )
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="No pending invite found.")

    # 2. Mark it as read (declined)
    notif.is_read = True

    session.commit()
    return {"detail": "Project invitation declined successfully."}