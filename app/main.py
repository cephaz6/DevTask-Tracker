# main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers - assuming these imports are correct based on your file structure
from routers import auth_router as auth
from routers.tasks.routes import router as task_router
from routers import tag_router
from routers.project.routes import router as project_router
from routers.comment_router import router as comment_router
from routers.notification_router import router as notification_router
from routers.dashboard.dashboard_router import router as dashboard_router
from routers.websocket import ws_comments # Import WebSocket handlers
from routers.copilot.copilot_router import router as copilot_router

# Utilities
from utils.scheduler import scheduler

# Load environment variables (already present, good!)
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    This is where we'll run database migrations.
    """
    yield

app = FastAPI(lifespan=lifespan)

# CORS Configuration - Fixed origins
origins = [
    "http://localhost:5173",  # frontend origin local
    "http://localhost:3000",  # alternative local port
    "https://devtask-client.vercel.app",  # REMOVED trailing slash
    "https://*.vercel.app",  # Allow all Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Root endpoint (your existing logic)
@app.get("/")
def root():
    return {"message": "Welcome to DevTask Tracker"}

# Include the routers (your existing logic)
app.include_router(auth.router)
app.include_router(tag_router.router)
app.include_router(task_router)
app.include_router(project_router)
app.include_router(comment_router)
app.include_router(notification_router)
app.include_router(dashboard_router)
app.include_router(ws_comments.router)
app.include_router(copilot_router)