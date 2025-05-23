from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models.tag import Tag
from schemas.tag import TagCreate, TagRead
from db.database import get_session

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=TagRead)
def create_tag(tag: TagCreate, session: Session = Depends(get_session)):
    db_tag = session.exec(select(Tag).where(Tag.name == tag.name)).first()
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    new_tag = Tag(name=tag.name)
    session.add(new_tag)
    session.commit()
    session.refresh(new_tag)
    return new_tag

@router.get("/", response_model=list[TagRead])
def read_tags(session: Session = Depends(get_session)):
    tags = session.exec(select(Tag)).all()
    return tags
