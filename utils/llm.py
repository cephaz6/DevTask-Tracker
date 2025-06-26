# services/llm.py

from datetime import date
from openai import OpenAI
from typing import List
from schemas.copilot import TaskRequestInput, TaskResponseItem, GeneratedProject
import json
import os

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_prompt(data: TaskRequestInput) -> str:
    return f"""
You are a project planning assistant.

The user wants to create a learning project titled "{data.title}".
They are a {data.level} learner and prefer a {data.tone} tone.
They can commit {data.hours_per_day} hours per day.
They want the project to start on {data.start_date}.
{'Include' if data.include_weekends else 'Exclude'} weekends when scheduling.

Please:
- Generate a series of learning tasks spread across days
- Return exactly one task per active day
- Use realistic task titles and short descriptions
- Include estimated_time (≤ hours/day), priority ("low", "medium", "high"), and due_date
- Format output as valid JSON (no comments, no code blocks)

Return a JSON like:
{{
  "title": "...",
  "description": "...",
  "tasks": [
    {{
      "title": "...",
      "description": "...",
      "estimated_time": ...,
      "priority": "...",
      "due_date": "YYYY-MM-DD"
    }}
  ]
}}
"""

def call_gpt_from_user_prompt(prompt: str) -> GeneratedProject:
    system_message = (
        "You are an intelligent task planner. "
        "Based on the user's description of what they want to learn or achieve, "
        "create a structured project with a title, short description, and a list of tasks. "
        "Each task should include title, description, estimated_time (in hours), priority (low/medium/high), and due_date. "
        "Return the response as valid JSON."
    )

    response = openai.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(content)
        return GeneratedProject(**parsed)
    except Exception as e:
        raise ValueError(f"GPT response could not be parsed: {e}\nRaw output:\n{content}")
