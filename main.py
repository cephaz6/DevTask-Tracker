from fastapi import FastAPI
from fastapi.params import Body  
from pydantic import BaseModel
from typing import Optional



app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/posts")
def get_posts():
    return [
        {"data": "This is a sample post 1"},
        {"data": "This is a sample post 2"},
        {"data": "This is a sample post 3"},
    ]

@app.post("/createposts")
def create_posts(post: Post):
    print(post)
    print(post.model_dump())
    
    return {"data": f"Post created with title: {post.title} and content: {post.content}"}