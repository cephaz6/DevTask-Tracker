from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.database import init_db
from routers import auth_router as auth
from routers.tasks.routes import router as task_router
from routers import tag_router
from routers.project.routes import router as project_router
from routers.comment_router import router as comment_router
from routers.notification_router import router as notification_router


from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Welcome to DevTask Tracker"}

# Include the routers
# app.include_router(task_router.router)
app.include_router(auth.router)
app.include_router(tag_router.router)
app.include_router(task_router)
app.include_router(project_router)
app.include_router(comment_router)
app.include_router(notification_router)


