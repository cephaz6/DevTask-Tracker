from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload 
from db.database import get_session
from utils.security import get_current_user
from sqlalchemy import select  
from typing import Optional

from models.project import ProjectMember, Project
from models.user import User
from schemas.project import ProjectMemberCreate,ProjectMemberRemoveRequest, ProjectMemberReadWithUser, ProjectMemberRead, ProjectRoleUpdate

router = APIRouter()


# Invite a user to a project    `POST /project-members/invite`
@router.post("/invite", response_model=ProjectMemberRead)
def invite_user_to_project(
    invite: ProjectMemberCreate, # Expects ProjectMemberCreate with 'user_identifier'
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

        # 3. Find the invited user by user_identifier (ID or email)
        invited_user: Optional[User] = None
        user_identifier_trimmed = invite.user_identifier.strip()

        if "@" in user_identifier_trimmed:
            # If it contains '@', assume it's an email
            invited_user = session.exec(
                select(User).where(User.email == user_identifier_trimmed)
            ).scalar_one_or_none() # Changed .first() to .scalar_one_or_none()
        else:
            # Otherwise, assume it's a user_id
            invited_user = session.exec(
                select(User).where(User.user_id == user_identifier_trimmed)
            ).scalar_one_or_none() # Changed .first() to .scalar_one_or_none()

        # Debugging print (remove in production)
        print(f"DEBUG: user_identifier_trimmed={user_identifier_trimmed}, invited_user={invited_user}")

        # Ensure the invited user was found
        if not invited_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invited user not found with the provided identifier.")

        # At this point, invited_user is guaranteed to be a User object.
        actual_invited_user_id = invited_user.user_id

        # 4. Prevent self-invitation
        if actual_invited_user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot invite yourself to a project."
            )

        # 5. Prevent duplicate invitations
        existing_member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == invite.project_id,
                ProjectMember.user_id == actual_invited_user_id, # Use the confirmed user ID
            )
        ).scalar_one_or_none() # Changed .first() to .scalar_one_or_none()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this project."
            )

        # 6. All checks passed, create the new project member
        member = ProjectMember(
            user_id=actual_invited_user_id, # Use the actual user_id from the found User object
            project_id=invite.project_id,
            role=invite.role # Use the role specified in the invitation payload
        )
        session.add(member)
        session.commit()
        session.refresh(member)
        return member

    except HTTPException as http_e:
        session.rollback()
        raise http_e # Re-raise FastAPI's HTTPExceptions directly
    except Exception as e:
        session.rollback()
        # Log unexpected errors for debugging
        print(f"An unexpected error occurred during project member invitation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected server error occurred: {str(e)}")



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
