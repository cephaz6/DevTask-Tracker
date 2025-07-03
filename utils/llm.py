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
- Use clear, realistic task titles and detailed descriptions
- In each description:
  - Explain exactly what the user should do
  - Provide context and helpful advice
  - Suggest free online resources like YouTube, W3Schools, MDN, or articles

Each task must include:
- title
- rich description with resources
- estimated_time (≤ {data.hours_per_day} hours)
- priority ("low", "medium", or "high")
- due_date (on or after {data.start_date}, and never before {today})

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
    today = date.today().isoformat()

    system_message = f"""
You are a professional AI project planner.

Today's date is {today}. If the user says "starting today" or gives a vague date like "June 30th", assume they mean the nearest future instance of that date. Never use dates in the past.

Your job is to:
- Understand what the user wants to learn or achieve
- Extract or infer duration (e.g. "3 months") and daily schedule (e.g. "2 to 4 hours per day")
- Generate a full set of tasks spread across the timeline, excluding weekends if specified

Each task must include:
- title
- a rich description:
  - explain exactly what the user should do
  - give context, advice, and helpful steps
  - suggest free online resources (e.g., YouTube videos, W3Schools, MDN, articles, etc.)
- estimated_time (in hours)
- priority (low, medium, or high)
- due_date (in YYYY-MM-DD format)

⚠️ Rules:
- Spread tasks evenly over the given period
- Do NOT generate any due_date before {today}
- Output a valid JSON object only (no markdown or code blocks)

Respond in this format:
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
