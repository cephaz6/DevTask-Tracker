# schemas/copilot.py

from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime, date

class AIGeneratedTask(BaseModel):
    title: str
    description: Optional[str]
    priority: Literal["low", "medium", "high"]
    estimated_time: float
    due_date: datetime

class AIGeneratedProject(BaseModel):
    title: str
    description: Optional[str]
    tasks: List[AIGeneratedTask]

class TaskRequestInput(BaseModel):
    title: str
    level: Literal["beginner", "intermediate", "advanced"]
    tone: str
    hours_per_day: float
    include_weekends: bool
    start_date: date

class TaskResponseItem(BaseModel):
    title: str
    description: str
    priority: Literal["low", "medium", "high"]
    estimated_time: float
    due_date: date

class GeneratedProject(BaseModel):
    title: str
    description: str
    tasks: List[TaskResponseItem]

class PromptRequest(BaseModel):
    prompt: str
