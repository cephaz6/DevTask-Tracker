from pydantic import BaseModel


# Base schema with common fields
class TagBase(BaseModel):
    name: str


# Schema used when creating a new tag
class TagCreate(TagBase):
    pass


# Schema used when reading tags (e.g. returning from API)
class TagRead(TagBase):
    id: str

    class Config:
        orm_mode = True


# Optional: For nested relations inside TaskRead schema
class TagReadNested(TagRead):
    pass
