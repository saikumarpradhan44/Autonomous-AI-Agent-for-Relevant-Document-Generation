# Autonomous AI Agent for Document Generation

An autonomous AI agent built with Python, FastAPI, and Groq LLMs that understands user requests, generates its own task plan, executes tasks, evaluates the generated content through a reflection mechanism, and produces professionally formatted Word documents.

## Project Overview

The Autonomous AI Agent automates document creation through a structured planning and execution workflow.

Instead of requiring users to manually define individual tasks, the agent analyzes the request, creates a sequence of tasks, executes them, evaluates the generated content, and generates a final `.docx` document.

## Key Features

- **Autonomous Task Planning:** Generates a task plan based on the user's request.
- **Task Execution:** Executes the generated tasks using a Groq-powered LLM.
- **Reflection and Self-Check:** Evaluates generated content for relevance, completeness, technical consistency, and quality.
- **Content Validation:** Checks task completion and verifies that content exists.
- **Word Document Generation:** Creates professionally formatted `.docx` documents.
- **REST API:** Provides an API endpoint through FastAPI for submitting requests and retrieving results.
- **Document Download:** Allows users to download generated Word documents.

## System Architecture

The agent follows this workflow:

1. User submits a request.
2. FastAPI receives the request.
3. Groq LLM generates an autonomous task plan.
4. The agent executes each task.
5. Generated content undergoes validation.
6. Reflection evaluates the content and suggests improvements.
7. The document generator creates a formatted Word document.
8. The API returns the execution results and document download endpoint.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| LLM Provider | Groq |
| Language Model | openai/gpt-oss-20b |
| Data Validation | Pydantic |
| Document Generation | python-docx |
| Environment Management | Python Virtual Environment |
| API Testing | Swagger UI |

## Project Structure

```text
Autonomous-AI-Agent/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   └── document_generator.py
│
├── notebooks/
│   └── agent_development.ipynb
│
├── outputs/
│
├── tests/
│
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Autonomous-AI-Agent
```

### 2. Create a virtual environment

```bash
python -m venv autonomous
```

Activate it on Windows:

```bash
autonomous\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Obtain an API key from the Groq developer console.

### 5. Start the FastAPI application

```bash
python -m uvicorn app.main:app --reload
```

The application will run at:

`http://127.0.0.1:8000`

## API Usage

### POST /agent

Accepts a user request and starts the autonomous agent workflow.

**Request body:**

```json
{
  "request": "Create a professional project proposal for an AI-powered student attendance management system. Include objectives, scope, technology stack, implementation timeline, estimated budget, risks, and expected outcomes."
}
```

**Example response fields:**

- `document_title`
- `document_type`
- `document_filename`
- `document_download_url`
- `task_plan`
- `task_results`
- `initial_validation`
- `reflection_reports`
- `final_validation`
- `completed_tasks`
- `total_tasks`

### GET /documents/{filename}

Downloads the generated Word document.

### GET /

Checks whether the API is running.

## API Documentation

FastAPI provides interactive API documentation through Swagger UI.

Open:

`http://127.0.0.1:8000/docs`

Use the Swagger interface to submit requests, execute the agent, and inspect the responses.

## Engineering Improvement: Reflection and Self-Check

The project implements a reflection mechanism as its engineering improvement.

After task execution, the agent evaluates the generated content based on:

- Relevance to the requested task.
- Completeness of the content.
- Technical consistency.
- Unsupported assumptions or claims.
- Clarity and professional quality.

Based on the reflection feedback, the agent can revise the generated content before final document generation.

## Testing

The agent was evaluated using two different scenarios:

**Test Case 1: Project Proposal Generation**

Generated a professional proposal for an AI-powered student attendance management system, covering objectives, scope, technology stack, timeline, budget, risks, and expected outcomes.

**Test Case 2: AI Implementation Planning**

Generated an implementation plan for a small college with a limited budget and a three-month deadline, including cloud versus local hosting comparisons, cost estimates, implementation phases, risks, and a fallback plan.

Both test cases completed successfully, with all generated tasks passing the final content validation checks.

## Security Notes

- Store API credentials in `.env`.
- Never commit `.env` or expose API keys in public repositories.
- Use `.env.example` as a template without real credentials.

## Author

Sai Kumar Pradhan
M.Tech – Computer Science and Engineering
**Project:** Autonomous AI Agent for Document Generation
