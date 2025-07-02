from datetime import date
from openai import OpenAI
from schemas.copilot import TaskRequestInput, GeneratedProject
import json
import os

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_prompt(data: TaskRequestInput) -> str:
    today = date.today().isoformat()

    return f"""
You are a project planning assistant.

Today's date is {today}.
The user wants to create a learning project titled "{data.title}".
They are a {data.level} learner and prefer a {data.tone} tone.
They can commit {data.hours_per_day} hours per day.
The project should start on {data.start_date}.
{"Include" if data.include_weekends else "Exclude"} weekends when scheduling.

Your job:
- Generate a list of tasks spread across active days starting from the project start date
- Only one task per active day
- Use clear, realistic task titles and short descriptions
- Assign each task:
  - estimated_time (≤ {data.hours_per_day} hours),
  - priority ("low", "medium", "high"),
  - due_date starting from {data.start_date} and not before {today}
- Ensure due_dates are realistic and spaced according to the active days

⚠️ Rules:
- Do NOT return any dates before {today}
- Output valid JSON only (no markdown, no comments)

Respond in this exact JSON format:
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
