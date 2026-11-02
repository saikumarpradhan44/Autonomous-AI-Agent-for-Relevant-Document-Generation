from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
import re

from app.agent import (
    generate_plan,
    execute_all_tasks,
    validate_task_results,
    improve_all_tasks
)

from app.document_generator import generate_document

app = FastAPI(
    title="Autonomous AI Agent",
    description="An autonomous AI agent for planning and executing tasks.",
    version="1.0.0"
)

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs"

class AgentRequest(BaseModel):
    request: str = Field(
        ...,
        min_length=10,
        description="Describe the task to be completed."
    )


@app.get("/")
def home():
    return {
        "message": "Autonomous AI Agent API is running!"
    }


@app.post("/agent")
def run_agent(payload: AgentRequest):
    try:
        # 1. Generate task plan
        plan = generate_plan(payload.request)

        # 2. Execute all tasks
        results = execute_all_tasks(plan)

        # 3. Validate generated content
        validation = validate_task_results(results)

        # 4. Reflect and improve content
        results, reflections = improve_all_tasks(
            plan,
            results
        )

        # 5. Final validation after improvement
        final_validation = validate_task_results(results)

        # 6. Check final validation
        if not all(item["passed"] for item in final_validation):
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Document generation stopped because some tasks failed validation.",
                    "validation": final_validation
                }
            )

        # 7. Prepare document sections
        sections = [
            {
                "heading": result.title,
                "content": result.content
            }
            for result in results
            if result.status == "completed" and result.content
        ]

        # 8. Generate a safe filename
        safe_title = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            plan.document_title
        ).strip("_")

        filename = f"{safe_title}.docx"
        document_path = OUTPUT_DIR / filename

        # 9. Generate Word document
        generate_document(
            title=plan.document_title,
            sections=sections,
            output_path=document_path
        )

        return {
            "document_title": plan.document_title,
            "document_type": plan.document_type,
            "document_filename": filename,
            "document_download_url": f"/documents/{filename}",
            "task_plan": [
                task.model_dump()
                for task in plan.tasks
            ],
            "task_results": [
                result.model_dump()
                for result in results
            ],
            "initial_validation": validation,
            "reflection_reports": reflections,
            "final_validation": final_validation,
            "completed_tasks": sum(
                result.status == "completed"
                for result in results
            ),
            "total_tasks": len(results)
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )


@app.get("/documents/{filename}")
def download_document(filename: str):

    # Prevent directory traversal
    if Path(filename).name != filename or not filename.endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Invalid document filename."
        )

    document_path = OUTPUT_DIR / filename

    if not document_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return FileResponse(
        path=document_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )    