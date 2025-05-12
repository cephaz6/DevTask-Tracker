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
    access_token = create_access_token(data={"sub": db_user.email})

    return {"access_token": access_token, "token_type": "bearer"}


# Get current user (after logging in)
@router.get("/me", response_model=UserRead)
def get_user(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return current_user


# Update user profile
@router.put("/update", response_model=UserRead)
def update_user_profile(user_update: UserUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Update user details
    statement = select(User).where(User.id == current_user.id)
    db_user = session.exec(statement).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.full_name = user_update.full_name or db_user.full_name
    db_user.email = user_update.email or db_user.email
    session.commit()

    return db_user
