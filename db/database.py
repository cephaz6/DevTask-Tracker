<<<<<<< HEAD
from sqlmodel import create_engine, Session, SQLModel
=======
from sqlmodel import create_engine, Session
>>>>>>> a5bd8487c91f1e5247a15fbd694a109d3215c472
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Get the database URL from environment variables
<<<<<<< HEAD
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devtask.db")
=======
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devtask_tracker.db")
>>>>>>> a5bd8487c91f1e5247a15fbd694a109d3215c472
engine = create_engine(DATABASE_URL, echo=True)


# Dependency to get a session
def get_session():
    with Session(engine) as session:
        yield session


# Function to create the database tables
def init_db():
<<<<<<< HEAD
    SQLModel.metadata.create_all(engine)
=======
    # SQLModel.metadata.create_all(engine)
>>>>>>> a5bd8487c91f1e5247a15fbd694a109d3215c472
    pass
