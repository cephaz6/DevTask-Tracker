from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from models.user import User
from schemas.user import UserCreate, UserRead
from db.database import get_session
from utils.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    # check if user already exists
    statement = select(User).where(User.email == user.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # hash the password and create the user
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user
