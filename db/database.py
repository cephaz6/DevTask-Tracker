from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devtask.db")
engine = create_engine(DATABASE_URL, echo=True)


# Dependency to get a session
def get_session():
    with Session(engine) as session:
        yield session


# Function to create the database tables
def init_db():
    SQLModel.metadata.create_all(engine)
    pass
