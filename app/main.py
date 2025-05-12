from fastapi import FastAPI
from contextlib import asynccontextmanager

from db.database import init_db
from routers import task_router
from routers import auth_router as auth

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # Cleanup code to be added here later.


app = FastAPI(lifespan=lifespan)

# Include the routers
app.include_router(task_router.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to DevTask Tracker"}
