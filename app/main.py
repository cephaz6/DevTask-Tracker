from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.database import init_db
from routers import task_router
from routers import auth_router as auth
from routers import tag_router

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

# Include the routers
app.include_router(task_router.router)
app.include_router(auth.router)
app.include_router(tag_router.router)

@app.get("/")
def root():
    return {"message": "Welcome to DevTask Tracker"}
