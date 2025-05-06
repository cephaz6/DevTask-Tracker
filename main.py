from fastapi import FastAPI
from fastapi.params import Body  
from pydantic import BaseModel
from typing import Optional
from random import randrange 



app = FastAPI()

class Post(BaseModel):
    id: int = randrange(0, 1000000)
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


my_posts = [
    {"id": 1, "title": "Post 1", "content": "Content of post 1", "published": True, "rating": 5},
    {"id": 2, "title": "Post 2", "content": "Content of post 2", "published": False, "rating": 3},
    {"id": 3, "title": "Post 3", "content": "Content of post 3", "published": True, "rating": 4},   
]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/posts")
def get_posts():
    return {"posts": my_posts}

@app.post("/createposts")
def create_posts(post: Post):
    print(post)
    print(post.model_dump())
    my_posts.append(post.model_dump())
    return {"data": f"Post created with title: {post.title} and content: {post.content}"}