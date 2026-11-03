import os
import json
import re

from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

from pathlib import Path

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = "openai/gpt-oss-120b"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# Task schema
class Task(BaseModel):
    task_id: int
    title: str
    description: str
    status: str = "pending"


# Agent plan schema
class AgentPlan(BaseModel):
    document_type: str
    document_title: str
    tasks: List[Task]


# Task execution result
class TaskResult(BaseModel):
    task_id: int
    title: str
    status: str
    content: Optional[str] = None
    error: Optional[str] = None

def generate_plan(user_request: str) -> AgentPlan:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
                You are an autonomous AI project planner.
                Break the user's request into clear, executable tasks.

                Return ONLY valid JSON in this structure:
                {
                    "document_type": "string",
                    "document_title": "string",
                    "tasks": [
                        {
                            "task_id": 1,
                            "title": "string",
                            "description": "string",
                            "status": "pending"
                        }
                    ]
                }

                Generate 5 to 12 relevant tasks.
                Do not include Markdown or explanations outside JSON.
                """
            },
            {"role": "user", "content": user_request}
        ],
        temperature=0.2,
        max_completion_tokens=2000
    )

    raw_plan = response.choices[0].message.content
    plan_data = json.loads(raw_plan)

    return AgentPlan.model_validate(plan_data)

def execute_task(task: Task, document_title: str) -> TaskResult:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical project proposal writer. "
                        "Generate clear, detailed, and professional content "
                        "for the assigned project section."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
                    Project: {document_title}
                    Section: {task.title}
                    Task Description: {task.description}

                    Write professional, relevant content for this section.
                    Use headings and bullet points wherever appropriate.
                    Avoid inventing facts. Clearly label estimates and assumptions.
                    """
                }
            ],
            temperature=0.3,
            max_completion_tokens=4000
        )

        content = response.choices[0].message.content
        

        if not content or not content.strip():
            raise ValueError("The model returned empty content.")

        task.status = "completed"

        return TaskResult(
            task_id=task.task_id,
            title=task.title,
            status="completed",
            content=content,
            
        )

    except Exception as e:
        task.status = "failed"

        return TaskResult(
            task_id=task.task_id,
            title=task.title,
            status="failed",
            error=str(e)
            
        )

def execute_all_tasks(agent_plan: AgentPlan) -> list[TaskResult]:
    results = []

    for task in agent_plan.tasks:
        print(f"Executing task {task.task_id}: {task.title}")

        result = execute_task(task, agent_plan.document_title)
        results.append(result)

        print(f"Status: {result.status}")

        if result.error:
            print(f"Error: {result.error}")

    return results

def validate_task_results(
    task_results: list[TaskResult]
) -> list[dict]:

    validation_report = []

    for result in task_results:

        checks = {
            "completed": result.status == "completed",
            "content_exists": bool(
                result.content and result.content.strip()
            )
        }

        validation_report.append({
            "task_id": result.task_id,
            "title": result.title,
            "checks": checks,
            "passed": all(checks.values())
        })

    return validation_report




def reflect_on_task(task: Task, content: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
                You are a strict quality reviewer.

                Evaluate the generated content for:
                1. Relevance to the task
                2. Completeness
                3. Technical consistency
                4. Unsupported claims or assumptions
                5. Clarity and professional quality

                Give a Quality Score out of 10.
                Provide specific improvement suggestions.
                Be critical and do not automatically give high scores.
                """
            },
            {
                "role": "user",
                "content": f"""
                Task: {task.title}
                Description: {task.description}

                Generated Content:
                {content}

                Review this content and provide your assessment.
                """
            }
        ],
        temperature=0.2,
        max_completion_tokens=1000
    )

    reflection = response.choices[0].message.content

    if not reflection or not reflection.strip():
        raise ValueError("The model returned an empty reflection.")

    return reflection.strip()



def revise_task_content(
    task: Task,
    original_content: str,
    reflection: str
) -> str:

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": """
                You are an expert technical writer.
                Improve the supplied content using the review feedback.

                Preserve accurate information.
                Do not invent facts, figures, or unsupported claims.
                Clearly label assumptions and estimates.
                Return only the revised content.
                """
            },
            {
                "role": "user",
                "content": f"""
                Task: {task.title}

                Original Content:
                {original_content}

                Review Feedback:
                {reflection}

                Produce the improved version.
                """
            }
        ],
        temperature=0.2,
        max_completion_tokens=1800
    )

    revised_content = response.choices[0].message.content

    if not revised_content or not revised_content.strip():
        raise ValueError("Revision returned empty content.")

    return revised_content


def improve_all_tasks(
    agent_plan: AgentPlan,
    task_results: list[TaskResult]
) -> tuple[list[TaskResult], list[str]]:


    reflection_reports = []

    for result in task_results:
        if result.status != "completed" or not result.content:
            continue

        task = next(
            (t for t in agent_plan.tasks if t.task_id == result.task_id),
            None
        )

        if task is None:
            continue

        print(f"Reviewing task {task.task_id}: {task.title}")

        try:
            reflection = reflect_on_task(task, result.content)
            reflection_reports.append(reflection)

            score_match = re.search(
                r"Quality\s*Score\s*[*:_-]*\s*(\d+(?:\.\d+)?)",
                reflection,
                re.IGNORECASE
            )

            score = float(score_match.group(1)) if score_match else None

            if score is not None and score < 8:
                print(f"Score: {score}/10. Revising content...")

                revised_content = revise_task_content(
                    task,
                    result.content,
                    reflection
                )

                if revised_content and revised_content.strip():
                    result.content = revised_content
                    print("Revision completed.")
                else:
                    print("Revision returned empty content. Keeping original content.")

                print("Revision completed.")

            else:
                print(f"Score: {score if score is not None else 'Unavailable'}/10.")

        except Exception as e:
            reflection_reports.append(
                f"Review failed for task {task.task_id}: {str(e)}"
            )

    return task_results, reflection_reports
    