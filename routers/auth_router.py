from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from models.user import User
from schemas.user import UserCreate, UserRead, UserUpdate
from db.database import get_session
from utils.security import hash_password, verify_password, create_access_token  
from datetime import datetime
from utils.security import get_current_user



router = APIRouter(prefix="/auth", tags=["Auth"])

# Register route
@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


# Login route
@router.post("/login")
def login_user(user: UserCreate, session: Session = Depends(get_session)):
    statement = select(User).where(User.email == user.email)
    db_user = session.exec(statement).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Username or Password")

    # Update last login time
    db_user.last_login = datetime.now()
    session.commit()

    # Generate JWT token
    access_token = create_access_token(data={"sub": db_user.user_id})

    return {"access_token": access_token, "token_type": "bearer", "sub": db_user.user_id}


# Get current user (after logging in)
@router.get("/me", response_model=UserRead)
def get_user(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Create a dictionary that matches the UserRead schema
    return {
        "user_id": current_user.user_id, 
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
    
    }


# Update user profile
@router.patch("/update", response_model=UserRead, summary="Update current user's profile")
def update_user_profile(
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the profile of the currently authenticated user.
    Only fields provided in the request body will be updated.
    """

    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    if user_update.email is not None:
        email_exists = session.exec(select(User).where(User.email == user_update.email)).first()
        if email_exists and email_exists.user_id != current_user.user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    current_user.updated_at = datetime.now() 

    if user_update.password is not None:
        current_user.hashed_password = hash_password(user_update.password)


    session.add(current_user) 
    session.commit() 
    session.refresh(current_user) 

    return current_user 
