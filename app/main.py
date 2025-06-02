from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routers import auth_router as auth
from routers.tasks.routes import router as task_router
from routers import tag_router
from routers.project.routes import router as project_router
from routers.comment_router import router as comment_router
from routers.notification_router import router as notification_router
from routers.dashboard.dashboard_router import router as dashboard_router
from routers.websocket import ws_comments  # Import WebSocket handlers

#Utilities
from utils.scheduler import scheduler

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    if not scheduler.running:
        scheduler.start()
        print("Background scheduler started.")

    yield

    # SHUTDOWN
    scheduler.shutdown()
    print("Background scheduler shut down.")


app = FastAPI(lifespan=lifespan)

# Optional: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
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
app.include_router(dashboard_router)
app.include_router(ws_comments.router)  


